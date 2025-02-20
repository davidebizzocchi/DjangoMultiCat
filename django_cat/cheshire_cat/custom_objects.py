import cheshire_cat_api as ccat
from typing import Dict, List, Optional, Tuple, Union, Any
from typing_extensions import Annotated
from pydantic import StrictBytes, validate_call, Field, StrictFloat, StrictStr, StrictInt
import io

from cheshire_cat_api.configuration import Configuration
from cheshire_cat_api.api import (
    EmbedderApi, LargeLanguageModelApi, MemoryApi, PluginsApi,
    RabbitHoleApi, SettingsApi, StatusApi
)
from cheshire_cat_api.api_client import ApiClient
from cheshire_cat_api.api_response import ApiResponse
from cheshire_cat_api.rest import RESTResponseType
import json

from cheshire_cat.types import AgentRequest

class CatRabbitHoleApi(RabbitHoleApi):
    @validate_call
    def upload_file(
        self,
        file: Union[StrictBytes, StrictStr],  # Remove BufferedReader
        chunk_size: Optional[StrictInt] = None,
        chunk_overlap: Optional[StrictInt] = None,
        metadata: Optional[Dict[str, Any]] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Upload File

        Upload a file containing text (.txt, .md, .pdf, etc.). File content will be extracted and segmented into chunks.
        Chunks will be then vectorized and stored into documents memory.

        :param file: File content as bytes or string
        :type file: Union[bytes, str]
        :param chunk_size: Maximum length of each chunk after the document is split (in tokens)
        :type chunk_size: int, optional
        :param chunk_overlap: Chunk overlap (in tokens)
        :type chunk_overlap: int, optional
        :param metadata: Metadata to be stored with each chunk
        :type metadata: dict, optional
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        """
        # Handle file-like objects
        if hasattr(file, 'read'):
            file = file.read()

        _param = self._upload_file_serialize(
            file=file,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata=metadata,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '422': "HTTPValidationError"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _upload_file_serialize(
        self,
        file,
        chunk_size,
        chunk_overlap,
        metadata,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params: Optional[bytes] = None

        # Add file to files
        if file is not None:
            _files['file'] = file

        # Add form parameters
        if chunk_size is not None:
            _form_params.append(('chunk_size', chunk_size))
        if chunk_overlap is not None:
            _form_params.append(('chunk_overlap', chunk_overlap))
        if metadata is not None:
            _form_params.append(('metadata', json.dumps(metadata)))

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='POST',
            resource_path='/rabbithole/',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

class CatMemoryApi(MemoryApi):
    @validate_call
    def get_working_memories_list(
        self,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Get Working Memories List
        
        Get list of available working memories

        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: override auth settings for request
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request
        :type _content_type: str, Optional
        :param _headers: override headers for request
        :type _headers: dict, optional
        :param _host_index: override host_index for request
        :type _host_index: int, optional
        :return: Returns the result object
        """

        _param = self._get_working_memories_list_serialize(
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _get_working_memories_list_serialize(
        self,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params: Optional[bytes] = None

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/memory/working_memories',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def get_working_memory(
        self,
        chat_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Get Working Memory
        
        Get a specific working memory

        :param chat_id: Working memory ID (required)
        :type chat_id: str
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: override auth settings for request
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request
        :type _content_type: str, Optional
        :param _headers: override headers for request  
        :type _headers: dict, optional
        :param _host_index: override host_index for request
        :type _host_index: int, optional
        :return: Returns the result object
        """

        _param = self._get_working_memory_serialize(
            chat_id=chat_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '404': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _get_working_memory_serialize(
        self,
        chat_id: str,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'chat_id': chat_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params: Optional[bytes] = None

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/memory/working_memories/{chat_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def delete_working_memory(
        self,
        chat_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Delete Working Memory
        
        Delete a specific working memory

        :param chat_id: Working memory ID (required)
        :type chat_id: str
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: override auth settings for request
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request 
        :type _content_type: str, Optional
        :param _headers: override headers for request
        :type _headers: dict, optional
        :param _host_index: override host index for request
        :type _host_index: int, optional
        :return: Returns the result object
        """

        _param = self._delete_working_memory_serialize(
            chat_id=chat_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '404': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _delete_working_memory_serialize(
        self,
        chat_id: str,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'chat_id': chat_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params: Optional[bytes] = None

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='DELETE', 
            resource_path='/memory/working_memories/{chat_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def wipe_conversation_history_by_chat(
        self,
        chat_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Wipe Conversation History
        
        Wipe vector memory points for a specific chat_id

        :param chat_id: Chat ID (required)
        :type chat_id: str
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: override auth settings for request
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request
        :type _content_type: str, Optional
        :param _headers: override headers for request
        :type _headers: dict, optional
        :param _host_index: override host index for request
        :type _host_index: int, optional
        :return: Returns the result object
        """

        _param = self._wipe_conversation_history_serialize_by_chat(
            chat_id=chat_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '404': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _wipe_conversation_history_serialize_by_chat(
        self,
        chat_id: str,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'chat_id': chat_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params: Optional[bytes] = None

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='DELETE',
            resource_path='/memory/conversation_history/{chat_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def update_points_metadata(
        self,
        collection_id: StrictStr,
        search: Dict[StrictStr, Any] = {},
        update: Dict[StrictStr, Any] = {},
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Update points metadata in a collection by metadata filter
        
        :param collection_id: Collection ID (required)
        :type collection_id: str
        :param search: Metadata filter to search points
        :type search: dict
        :param update: New metadata to update
        :type update: dict
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: override auth settings for request
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request
        :type _content_type: str, Optional
        :param _headers: override headers for request
        :type _headers: dict, optional
        :param _host_index: override host index for request
        :type _host_index: int, optional
        :return: Returns the result object
        """

        _param = self._update_points_metadata_serialize(
            collection_id=collection_id,
            search=search,
            update=update,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _update_points_metadata_serialize(
        self,
        collection_id: str,
        search: Dict[str, Any],
        update: Dict[str, Any],
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'collection_id': collection_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = {
            'search': search,
            'update': update
        }

        # set the HTTP header `Accept` and `Content-Type`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='PATCH',
            resource_path='/memory/collections/{collection_id}/points/metadata',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def get_points_by_metadata(
        self,
        collection_id: StrictStr,
        metadata: Dict[StrictStr, Any] = {},
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        """Get points filtered by metadata criteria
        
        :param collection_id: Collection ID (required)
        :type collection_id: str
        :param metadata: Metadata filter criteria
        :type metadata: dict
        :param _request_timeout: timeout setting for this request
        :type _request_timeout: int, tuple(int, int), optional
        :return: Returns the result object
        """

        _param = self._get_points_by_metadata_serialize(
            collection_id=collection_id,
            metadata=metadata,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _get_points_by_metadata_serialize(
        self,
        collection_id: str,
        metadata: Dict[str, Any],
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'collection_id': collection_id}
        _query_params: List[Tuple[str, str]] = []

        # Add metadata as query parameters
        if metadata:
            _query_params.extend([('metadata', json.dumps(metadata))])

        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = None

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])

        # authentication setting
        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/memory/collections/{collection_id}/points/by_metadata',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    @validate_call
    def edit_chat_to_points(
        self,
        collection_id: StrictStr,
        search_metadata: Dict[StrictStr, Any],
        chat_ids: List[StrictStr],
        mode: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._param_edit_chat_to_points(
            collection_id=collection_id,
            search_metadata=search_metadata,
            chat_ids=chat_ids,
            mode=mode,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _param_edit_chat_to_points(
        self,
        collection_id: str,
        search_metadata: Dict[str, Any],
        chat_ids: List[str],
        mode: str,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'collection_id': collection_id}
        _query_params: List[Tuple[str, str]] = [('mode', mode)]
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = {
            'search_metadata': search_metadata,
            'chats_id': chat_ids
        }

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='PATCH',
            resource_path='/memory/collections/{collection_id}/points/edit_chat_ids',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

class AgentsApi:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    def _list_agent_serialize(
        self,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = {
        }

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/agents',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    def _create_agent_serialize(
        self,
        data: Dict[StrictStr, Any],
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}

        _body_params = data

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='POST',
            resource_path='/agents',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )
    
    def _update_agent_serialize(
        self,
        agent_id: StrictStr,
        data: Dict[StrictStr, Any],
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'agent_id': agent_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = data

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='PATCH',
            resource_path='/agents/{agent_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    def _retrieve_agent_serialize(
        self,
        agent_id: StrictStr,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'agent_id': agent_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = {
        }

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/agents/{agent_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )

    def _delete_agent_serialize(
        self,
        agent_id: StrictStr,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> Tuple:
        _host = None
        _collection_formats: Dict[str, str] = {}
        _path_params: Dict[str, str] = {'agent_id': agent_id}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[str, str] = {}
        _body_params = {
        }

        _header_params['Accept'] = self.api_client.select_header_accept([
            'application/json'
        ])
        _header_params['Content-Type'] = self.api_client.select_header_content_type([
            'application/json'
        ])

        _auth_settings: List[str] = []

        return self.api_client.param_serialize(
            method='DELETE',
            resource_path='/agents/{agent_id}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )
    
    @validate_call
    def list_agents(
        self,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._list_agent_serialize(
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def create_agent(
        self,
        data: Dict[StrictStr, Any],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._create_agent_serialize(
            data=data,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def update_agent(
        self,
        agent_id: StrictStr,
        data: Dict[StrictStr, Any],
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._update_agent_serialize(
            agent_id=agent_id,
            data=data,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def retrieve_agent(
        self,
        agent_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._retrieve_agent_serialize(
            agent_id=agent_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def delete_agent(
        self,
        agent_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> object:
        _param = self._delete_agent_serialize(
            agent_id=agent_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "object",
            '400': "object"
        }
        
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

class CatClient(ccat.CatClient):
    def _connect_api(self):
        protocol = "https" if self._conn_settings.secure_connection else "http"
        config = Configuration(host=f"{protocol}://{self._conn_settings.base_url}:{self._conn_settings.port}")

        client = ApiClient(
            configuration=config,
            header_name='access_token',
            header_value=self._conn_settings.auth_key
        )

        client.set_default_header('user_id', self._conn_settings.user_id)

        self.memory = CatMemoryApi(client)
        self.plugins = PluginsApi(client)
        self.rabbit_hole = CatRabbitHoleApi(client)
        self.status = StatusApi(client)
        self.embedder = EmbedderApi(client)
        self.settings = SettingsApi(client)
        self.llm = LargeLanguageModelApi(client)
        self.agents = AgentsApi(client)

