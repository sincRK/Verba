import base64
import glob
import os
from datetime import datetime
from pathlib import Path

from wasabi import msg

from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

from goldenverba.components.reader.document import Document
from goldenverba.components.reader.interface import InputForm, Reader


class UnstructuredAPI(Reader):
    """
    The PDFReader reads .pdf files using Unstructured.
    """

    def __init__(self):
        super().__init__()
        self.file_types = [".pdf"]
        self.requires_env = ["UNSTRUCTURED_API_URL"]
        self.name = "UnstructuredAPIPDF"
        self.description = ("Reads PDF files powered by unstructured.io "
                            "via self hosted API.")
        self.input_form = InputForm.UPLOAD.value

    def load(
        self,
        bytes: list[str] = None,
        contents: list[str] = None,
        paths: list[str] = None,
        fileNames: list[str] = None,
        document_type: str = "Documentation",
    ) -> list[Document]:
        """Ingest data into Weaviate
        @parameter: bytes : list[str] - List of bytes
        @parameter: contents : list[str] - List of string content
        @parameter: paths : list[str] - List of paths to files
        @parameter: fileNames : list[str] - List of file names
        @parameter: document_type : str - Document type
        @returns list[Document] - Lists of documents.
        """
        if fileNames is None:
            fileNames = []
        if paths is None:
            paths = []
        if contents is None:
            contents = []
        if bytes is None:
            bytes = []
        documents = []

        # If paths exist
        if len(paths) > 0:
            for path in paths:
                if path != "":
                    data_path = Path(path)
                    if data_path.exists():
                        if data_path.is_file():
                            documents += self.load_file(
                                data_path, document_type
                            )
                        else:
                            documents += self.load_directory(
                                data_path, document_type
                            )
                    else:
                        msg.warn(f"Path {data_path} does not exist")

        # If bytes exist
        if len(bytes) > 0 and len(bytes) == len(fileNames):
            for byte, fileName in zip(bytes, fileNames):
                documents += self.load_bytes(byte, fileName, document_type)

        # If content exist
        if len(contents) > 0 and len(contents) == len(fileNames):
            for content, fileName in zip(contents, fileNames):
                document = Document(
                    name=fileName,
                    text=content,
                    type=document_type,
                    timestamp=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    reader=self.name,
                )
                documents.append(document)

        msg.good(f"Loaded {len(documents)} documents")
        return documents

    def load_bytes(
        self, 
        bytes_string, 
        fileName, 
        document_type: str
        ) -> list[Document]:
        """Loads a pdf bytes file
        @param bytes_string : str - PDF File bytes coming from the frontend
        @param fileName : str - Filename
        @param document_type : str - Document Type
        @returns list[Document] - Lists of documents.
        """
        documents = []

        # only address without /general/v0/general
        url = os.environ.get(
            "UNSTRUCTURED_API_URL", "172.17.0.1:8000"
        )
        
        unstructured_api_key = os.environ.get("UNSTRUCTURED_API_KEY", "")
        
        s = UnstructuredClient(
            server_url=url,
            api_key_auth=unstructured_api_key,
        )

        decoded_bytes = base64.b64decode(bytes_string)
        with open("reconstructed.pdf", "wb") as file:
            file.write(decoded_bytes)

        with open("reconstructed.pdf", "rb") as f:
            # Note that this currently only supports a single file
            files = shared.Files(
                content=f.read(),
                file_name=fileName,
            )
        
        req = shared.PartitionParameters(
            files=files,
            # Other partition params
            strategy='auto',
            languages=["eng", "de"],
        )

        try:
            resp = s.general.partition(req)
        except SDKError as e:
            print(e)

        json_response = resp.raw_response.json()

        full_content = ""

        for chunk in json_response:
            if "text" in chunk:
                text = chunk["text"]
                full_content += text + " "

        document = Document(
            text=full_content,
            type=document_type,
            name=str(fileName),
            link=str(fileName),
            timestamp=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            reader=self.name,
        )
        documents.append(document)
        msg.good(f"Loaded {str(fileName)}")
        os.remove("reconstructed.pdf")
        return documents

    def load_file(self, file_path: Path, document_type: str) -> list[Document]:
        """Loads .pdf file
        @param file_path : Path - Path to file
        @param document_type : str - Document Type
        @returns list[Document] - Lists of documents.
        """
        documents = []

        if file_path.suffix not in self.file_types:
            msg.warn(f"{file_path.suffix} not supported")
            return []

        # only address without /general/v0/general
        url = os.environ.get(
            "UNSTRUCTURED_API_URL", "172.17.0.1:8000"
        )
        
        unstructured_api_key = os.environ.get("UNSTRUCTURED_API_KEY", "")
        
        s = UnstructuredClient(
            server_url=url,
            api_key_auth=unstructured_api_key,
        )

        with open(file_path, "rb") as f:
            # Note that this currently only supports a single file
            files = shared.Files(
                content=f.read(),
                file_name=file_path.name,
            )
        
        req = shared.PartitionParameters(
            files=files,
            # Other partition params
            strategy='auto',
            languages=["eng", "de"],
        )

        try:
            resp = s.general.partition(req)
        except SDKError as e:
            msg.fail(f"Error: {e}")

        json_response = resp.raw_response.json()
        full_content = ""

        for chunk in json_response:
            if "text" in chunk:
                text = chunk["text"]
                full_content += text + " "

        document = Document(
            text=full_content,
            type=document_type,
            name=str(file_path),
            link=str(file_path),
            timestamp=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            reader=self.name,
        )
        documents.append(document)
        msg.good(f"Loaded {str(file_path)}")
        return documents

    def load_directory(self, dir_path: Path, document_type: str) -> list[Document]:
        """Loads .pdf files from a directory and its subdirectories.

        @param dir_path : Path - Path to directory
        @param document_type : str - Document Type
        @returns list[Document] - List of documents
        """
        # Initialize an empty dictionary to store the file contents
        documents = []

        # Convert dir_path to string, in case it's a Path object
        dir_path_str = str(dir_path)

        # Loop through each file type
        for file_type in self.file_types:
            # Use glob to find all the files in dir_path and 
            # its subdirectories matching the current file_type
            files = glob.glob(
                f"{dir_path_str}/**/*{file_type}", recursive=True
            )

            # Loop through each file
            for file in files:
                msg.info(f"Reading {str(file)}")
                with open(file, encoding="utf-8"):
                    documents += self.load_file(
                        file, document_type=document_type
                    )

        msg.good(f"Loaded {len(documents)} documents")
        return documents
