from io import StringIO
from typing import Dict, Any

import lxml.html
import pandas as pd

from .exceptions import HTMLParserError


class HTMLParser:
    # TODO with_xpath - if result is empty then either raise exception or return empty list?
    # TODO add xpath combined with regex
    # TODO check if df.empty pandas
    def with_xpath(
        self, xpath: str, html: str = None, root = None, index: int = 0, permissive=True
    ):
        """
        Parse HTML with XPath expression and return the result. If index is not None, return the value at the index.

        :param xpath: XPath expression
        :param html: HTML string
        :param root: lxml.html
        :param index: int
        :param permissive: bool
        :return: str or list

        :raises: HTMLParserError
        """
        if all([root is None, html is None]):
            raise AttributeError('Either "html" or "root" params have to be defined.')
        _tree = lxml.html.fromstring(html) if root is None else root

        result = _tree.xpath(xpath)

        if result is None:
            raise HTMLParserError(permissive=permissive)

        if not isinstance(result, list):
            return result
        
        result = [elem for elem in result if elem != '']
        # If user wants the whole results list as a return value
        if index is None:
            return result
        # Check if there is sufficient number of values in result
        return self.__check_enough_values(result, index, permissive)

    def with_pandas(
            self, html: str, index: int = 0, pandas_args: Dict[Any, Any] = None, permissive=True
    ):
        """
        Parse HTML with pandas and return the result. If index is not None, return the value at the index.

        :param html: HTML string
        :param index: int
        :param pandas_args: dict
        :param permissive: bool
        :return: pd.DataFrame or list

        :raises: HTMLParserError
        """
        pandas_args = pandas_args or {}

        if not isinstance(html, StringIO):
            html = StringIO(html)
        try:
            result = pd.read_html(html, **pandas_args)
        except ValueError:
            raise HTMLParserError(permissive=permissive)
        if index is None:
            return result
        # Check if there is sufficient number of values in result
        return self.__check_enough_values(result, index, permissive)

    def __check_enough_values(self, result, index, permissive):
        if len(result) <= index:
            _result = '\n'.join(result)
            raise HTMLParserError(
                f"Not enough values found in the result: [\n{_result}\n]", permissive=permissive
            )
        return result[index]
