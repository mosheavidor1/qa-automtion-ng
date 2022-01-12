from abc import abstractmethod

from infra.assertion.assertion import Assertion
from infra.system_components.management import Management


class BaseTest:

    management: Management = None

    @abstractmethod
    def prerequisites(self):
        pass

    @abstractmethod
    def run_and_validate(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    def play_test(self):
        try:
            self.prerequisites()
            self.run_and_validate()
            self.cleanup()
        except Exception as e:
            raise e
        finally:
            Assertion.assert_all()
