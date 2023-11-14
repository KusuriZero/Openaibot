# -*- coding: utf-8 -*-
# @Time    : 2023/8/16 下午8:54
# @Author  : sudoskys
# @File    : func_call.py
# @Software: PyCharm
import threading
from typing import List, Dict
from typing import Optional, Type
from typing import TYPE_CHECKING

from . import _openapi_version_, BaseTool, get_loaded_plugins, Plugin, get_plugin
from .schema import FuncPair
from ..schema import Function, File

if TYPE_CHECKING:
    from ...schema import RawMessage

threading_lock = threading.Lock()


class ToolRegister(object):
    """
    扩展对 _plugins 字段的操作,需要实例化以获取数据
    """

    def __init__(self):
        self.version = _openapi_version_
        self.pair_function: Dict[str, FuncPair] = {}
        self.plugins = get_loaded_plugins()
        self.__prepare()

    def __prepare(self):
        # 遍历所有插件
        for item in self.plugins:
            for sub_item in item.metadata.function:
                self.pair_function[sub_item.name] = sub_item

    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        if not self.pair_function.get(name, None):
            return None
        return self.pair_function[name].tool

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return get_plugin(name)

    @property
    def functions(self) -> Dict[str, Function]:
        _item: Dict[str, Function] = {}
        for item in self.plugins:
            for sub_item in item.metadata.function:
                _item[sub_item.name] = sub_item.function
        return _item

    @property
    def tools(self) -> List[Type[BaseTool]]:
        _item: List[Type[BaseTool]] = []
        for item in self.plugins:
            for sub_item in item.metadata.function:
                _item.append(sub_item.tool)
        return _item

    def filter_pair(self,
                    key_phrases: str,
                    message_raw: "RawMessage" = None,
                    file_list: List[File] = None,
                    ignore: List[str] = None
                    ) -> List[Function]:
        """
        过滤group中的函数
        """
        if ignore is None:
            ignore = []
        if file_list is None:
            file_list = []
        function_list = []

        def _match_file(_tool, _file_list):
            for file in _file_list:
                if _tool.file_match_required.match(file.file_name):
                    return True
            return False

        for func_name, pair_cls in self.pair_function.items():
            _tool_cls = pair_cls.tool()
            if _tool_cls.func_message(message_text=key_phrases, message_raw=message_raw):
                # 关键词大类匹配成功
                if func_name in ignore:
                    continue  # 忽略函数
                if _tool_cls.file_match_required:
                    if not _match_file(_tool_cls, file_list):
                        continue
                function_list.append(pair_cls.function)
        return function_list
