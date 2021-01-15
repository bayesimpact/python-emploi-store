import datetime
import typing


class Resource(object):
    def __init__(
            self,
            client: Client,
            name: typing.Optional[str] = None,
            **kwargs: typing.Any) -> None:
        ...

    def records(
            self,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            fields: typing.Optional[typing.Iterable[str]] = None) -> typing.Iterator:
        ...

    def to_csv(
            self,
            file_name: str,
            fieldnames: typing.Optional[typing.List[str]] = None,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            iterator: typing.Optional[typing.Callable[..., typing.Iterator]] = None
    ) -> None:
        ...


class Package(object):
    def __init__(
            self,
            client: Client,
            name: typing.Optional[str] = None,
            resources: typing.Optional[typing.List[typing.Dict[str, typing.Any]]] = None,
            **unused_kwargs: typing.Any) -> None:
        ...

    def list_resources(self) -> typing.List[str]:
        ...

    def get_resource(
            self,
            name: typing.Optional[str] = None,
            name_re: typing.Optional[typing.Pattern] = None,
            resource_id: typing.Optional[str] = None,
            pe_version: typing.Optional[str] = None) -> Resource:
        ...


class Client(object):

    api_url: str

    def __init__(
            self,
            client_id: typing.Optional[str] = None,
            client_secret: typing.Optional[str] = None) -> None:
        ...

    def access_token(
            self,
            scope: str,
            valid_for: datetime.timedelta = datetime.timedelta(seconds=5)) -> typing.Optional[str]:
        ...

    def api_get(self, action: str, **params: typing.Optional[typing.Union[str, int]]) \
            -> typing.Optional[typing.Dict[str, typing.Any]]:
        ...

    def list_packages(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        ...

    def get_package(
            self,
            name: typing.Optional[str] = None,
            package_id: typing.Optional[str] = None) -> Package:
        ...

    def get_lbb_companies(
            self,
            latitude: typing.Optional[float] = None,
            longitude: typing.Optional[float] = None,
            distance: float = 10,
            rome_codes: typing.Union[None, str, typing.List[str]] = None,
            naf_codes: typing.Union[None, typing.List[str]] = None,
            city_id: typing.Optional[str] = None,
            contract: typing.Optional[str] = None) -> typing.Iterator[typing.Dict[str, str]]:
        ...

    def get_employment_rate_rank_for_training(self, formacode: str, city_id: str) \
            -> typing.Dict[str, typing.Union[str, float]]:
        ...

    def get_match_via_soft_skills(self, rome: str) -> typing.Iterator[typing.Dict[str, typing.Any]]:
        ...

    def list_emploistore_services(self) -> typing.Dict[str, typing.Any]:
        ...

    def describe_emploistore_service(
            self,
            service_id: str,
            should_get_images: bool = False) -> typing.Dict[str, typing.Any]:
        ...

    def list_online_events(self) -> typing.Dict[str, typing.Any]:
        ...

    def list_physical_events(self) -> typing.Dict[str, typing.Any]:
        ...
