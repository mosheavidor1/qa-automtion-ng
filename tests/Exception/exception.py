import allure
import pytest

from tests.Exception import Exception_base


@allure.story("Collectors")
@allure.feature("Exceptions")
@pytest.mark.sanity
class Exceptions(Exception_base):

    @pytest.mark.xray('EN-68879')
    def test_Create_Full_covered_exception(self):
        pass