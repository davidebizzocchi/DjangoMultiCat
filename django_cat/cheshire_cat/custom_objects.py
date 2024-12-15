import cheshire_cat_api as ccat
from typing import Dict, List, Optional, Tuple, Union, Any
from typing_extensions import Annotated
from pydantic import validate_call, Field, StrictFloat, StrictStr, StrictInt

from cheshire_cat_api.configuration import Configuration
from cheshire_cat_api.api import (
    EmbedderApi, LargeLanguageModelApi, MemoryApi, PluginsApi,
    RabbitHoleApi, SettingsApi, StatusApi
)
from cheshire_cat_api.api_client import ApiClient
from cheshire_cat_api.api_response import ApiResponse
from cheshire_cat_api.rest import RESTResponseType


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
        self.rabbit_hole = RabbitHoleApi(client)
        self.status = StatusApi(client)
        self.embedder = EmbedderApi(client)
        self.settings = SettingsApi(client)
        self.llm = LargeLanguageModelApi(client)

