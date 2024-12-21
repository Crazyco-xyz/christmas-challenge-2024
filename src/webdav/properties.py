import abc
from datetime import datetime, timezone
from enum import Enum
import mimetypes
import os
from typing import Optional

import constants
from proj_types.file_type import FileType
from storage.datadb import DataDB
from proj_types.xml import XmlFragment, XmlString


class DavProp(abc.ABC):
    def __init__(self, name: str, namespace: str) -> None:
        self._name = name
        self._namespace = namespace

    @property
    def propname(self) -> str:
        """
        Returns:
            str: The name of the property
        """

        return self._name

    @property
    def namespace(self) -> str:
        """
        Returns:
            str: The namespace of the property
        """

        return self._namespace

    @abc.abstractmethod
    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        pass

    @abc.abstractmethod
    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        pass

    def get_property(self, file_id: str) -> XmlFragment:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The property if it exists, otherwise None
        """

        prop = self._get_property(file_id)
        return XmlFragment(self.propname, "D", [] if prop is None else [prop])

    @abc.abstractmethod
    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to
        """

        pass

    @abc.abstractmethod
    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        pass

    def root_property(self) -> XmlFragment:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The property if it exists, otherwise None
        """

        prop = self._root_property()
        return XmlFragment(self.propname, "D", [] if prop is None else [prop])


class CreationDate(DavProp):
    def __init__(self) -> None:
        super().__init__("creationdate", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        if file_id is None:
            return True

        return DataDB().files().is_file(file_id)

    def _creationdate(self, file: str) -> float:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587
        """
        if os.name == "nt":
            return os.path.getctime(file)
        else:
            stat = os.stat(file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def _make_webtime(self, unix: float) -> XmlString:
        return XmlString(
            datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return self._make_webtime(
            self._creationdate(os.path.join(constants.FILES, file_id))
        )

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class DisplayName(DavProp):
    def __init__(self) -> None:
        super().__init__("displayname", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        return True

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlString(DataDB().files().get_name(file_id))

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlString(constants.DAV_NAME)


class ResourceType(DavProp):
    def __init__(self) -> None:
        super().__init__("resourcetype", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        return True

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        match DataDB().files().file_type(file_id):
            case FileType.FILE:
                return None
            case FileType.FOLDER:
                return XmlFragment("collection", "D")

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlFragment("collection", "D")


class GetContentLength(DavProp):
    def __init__(self) -> None:
        super().__init__("getcontentlength", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        if file_id is None:
            return False

        return DataDB().files().is_file(file_id)

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlString(str(os.path.getsize(os.path.join(constants.FILES, file_id))))

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class GetContentType(DavProp):
    def __init__(self) -> None:
        super().__init__("getcontenttype", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        if file_id is None:
            return False

        return DataDB().files().is_file(file_id)

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlString(
            mimetypes.guess_type(DataDB().files().get_name(file_id))[0]
            or constants.MIME_FALLBACK
        )

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class GetLastModified(DavProp):
    def __init__(self) -> None:
        super().__init__("getlastmodified", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        if file_id is None:
            return True

        return DataDB().files().is_file(file_id)

    def _make_webtime(self, unix: float) -> str:
        return datetime.fromtimestamp(unix, tz=timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return XmlString(
            self._make_webtime(os.path.getmtime(os.path.join(constants.FILES, file_id)))
        )

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to
        """

        if not isinstance(data, XmlString):
            return

        s = data.text
        posix_time = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S GMT").timestamp()

        os.utime(os.path.join(constants.FILES, file_id), (posix_time, posix_time))

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class LockDiscovery(DavProp):
    def __init__(self) -> None:
        super().__init__("lockdiscovery", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        return True

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class SupportedLock(DavProp):
    def __init__(self) -> None:
        super().__init__("supportedlock", "D")

    def possible_for(self, file_id: Optional[str]) -> bool:
        """Checks if the property is possible for a given file

        Args:
            file_id (Optional[str]): The ID of the file to check

        Returns:
            bool: Whether the property is possible for the file
        """

        return True

    def _get_property(self, file_id: str) -> Optional[XmlFragment]:
        """Get the property for a file

        Args:
            file_id (str): The ID of the file to get the property for

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None

    def set_property(self, file_id: str, data: XmlFragment) -> None:
        """Set the property for a file

        Args:
            file_id (str): The ID of the file to set the property for
            data (XmlFragment): The data to set the property to

        Note:
            This property cannot be set
        """

    def _root_property(self) -> Optional[XmlFragment]:
        """Get the property for root

        Returns:
            Optional[XmlFragment]: The inner part of the property if it exists, otherwise None
        """

        return None


class DavProperties(Enum):
    CREATION_DATE = CreationDate()
    DISPLAY_NAME = DisplayName()
    RESOURCE_TYPE = ResourceType()
    CONTENT_LENGTH = GetContentLength()
    CONTENT_TYPE = GetContentType()
    LAST_MODIFIED = GetLastModified()
    LOCK_DISCOVERY = LockDiscovery()
    SUPPORTED_LOCK = SupportedLock()

    def __init__(self, cls: DavProp) -> None:
        self._prop = cls

    @staticmethod
    def allprop() -> list[DavProp]:
        """
        Returns:
            list[DavProp]: Returns all properties that fall into the allprop category
        """

        return [
            DavProperties.CREATION_DATE.value,
            DavProperties.DISPLAY_NAME.value,
            DavProperties.RESOURCE_TYPE.value,
            DavProperties.CONTENT_LENGTH.value,
            DavProperties.CONTENT_TYPE.value,
            DavProperties.LAST_MODIFIED.value,
            DavProperties.LOCK_DISCOVERY.value,
            DavProperties.SUPPORTED_LOCK.value,
        ]

    @staticmethod
    def get_prop(name: str) -> Optional[DavProp]:
        """Get a property by its propname

        Args:
            name (str): The name of the property

        Returns:
            Optional[DavProp]: The property if it exists, otherwise None
        """

        for n in DavProperties._member_names_:
            p = DavProperties[n]
            if p.prop.propname == name:
                return p.prop
        return None

    @property
    def prop(self) -> DavProp:
        return self._prop
