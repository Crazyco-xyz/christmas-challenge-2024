from typing import Optional

from proj_types.proto_error import ProtocolError


class XmlReturnError(Exception):
    def __init__(self, tagname: str) -> None:
        """The error thrown when a closing tag is encountered.

        Args:
            tagname (str): The name of the closing tag
        """

        super().__init__()
        self._tagname = tagname

    @property
    def tagname(self) -> str:
        """
        Returns:
            str: The name of the closing tag
        """

        return self._tagname


class XmlReader:
    def __init__(self, text: str) -> None:
        self._text = text.replace("\r", " ").replace("\n", " ")
        self._pos = 0

    def _read(self) -> str:
        """Reads the next character in the XML text

        Raises:
            EOFError: If the end of the XML text is reached

        Returns:
            str: The character read
        """

        # Advance position and check for EOF
        self._pos += 1
        if self._pos > len(self._text):
            raise EOFError("End of XML input during READ")

        # Read the chararcter
        return self._text[self._pos - 1]

    def _peek(self) -> str:
        """Peeks at the next character in the XML text

        Raises:
            EOFError: If the end of the XML text is reached

        Returns:
            str: The character peeked at
        """

        # Check for EOF
        if self._pos >= len(self._text) - 1:
            raise EOFError("End of XML input during PEEK")

        # Peek the character
        return self._text[self._pos]

    def _prev(self) -> str:
        """Reads the previous character in the XML text

        Raises:
            EOFError: If the beginning of the XML text is reached

        Returns:
            str: The character read
        """

        # Check for beginning of text
        if self._pos <= 0:
            raise EOFError("Beginning of XML input during PREV")

        # Peek the character
        return self._text[self._pos - 1]

    def _match(self, *expected: str) -> bool:
        """Checks if one of the expected characters is the next
        character in the XML text and advances the position if it is

        Returns:
            bool: Whether an expected character was encountered
        """

        # Check if the next character is one of the expected
        if self._peek() in expected:
            # Advance the cursor
            self._pos += 1
            return True

        return False

    def _skip_whitespace(self) -> None:
        """Skips all whitespace characters ahead of the cursor"""

        while self._peek() == " ":
            self._pos += 1

    def _read_text(self) -> "XmlString":
        """Reads text until a tag is encountered

        Returns:
            XmlFragment: The text read
        """

        # Create a string buffer
        st = []

        # Read until a tag is encountered
        while not self._match("<"):
            st.append(self._read())

        # Package the string into an XmlString fragment
        return XmlString("".join(st))

    def _read_name(self) -> str:
        """Reads the name of a tag

        Returns:
            str: The name of the tag
        """

        # Creates a string buffer
        st = [self._read()]

        # Read until one of the ending characters is encountered
        while not self._match(" ", ">", "/"):
            st.append(self._read())

        # Return the name
        return "".join(st)

    def _name_split(self, name: str) -> tuple[Optional[str], str]:
        """Splits the name into namespace and actual name

        Args:
            name (str): The name to split

        Returns:
            tuple[Optional[str], str]: The namespace and name
        """

        # Check if the name has a namespace
        if ":" not in name:
            return (None, name)

        # Split the name and return it
        ns, name = name.split(":", 1)
        return (ns, name)

    def _read_props(self, frag: "XmlFragment") -> None:
        """Reads all properties of a fragment

        Args:
            frag (XmlFragment): _description_
        """

        while True:
            prop = []
            in_quotes = False

            # Read until a space or closing tag is encountered
            while in_quotes or not self._match(" ", "/", ">"):
                c = self._read()

                # Check if the character is a quote
                if c == '"':
                    in_quotes = not in_quotes

                prop.append(c)

            prop = "".join(prop)

            # Check if the property is empty
            if "=" in prop:
                k, v = prop.split("=", 1)
                frag.properties[k] = v.strip('"')
            else:
                frag.properties[prop] = ""

            # Check if we encountered a closing tag and break
            if self._prev() in [">", "/"]:
                break

    def _skip(self, amount: int = 1) -> None:
        """Skips a certain amount of characters in the XML text

        Args:
            amount (int, optional): The amount of characters to skip. Defaults to 1.
        """

        self._pos += amount

    def _read_children(self, frag: "XmlFragment") -> None:
        """Reads all children of a fragment

        Args:
            frag (XmlFragment): The fragment to read children for

        Raises:
            XmlReturnError: If the closing tag encountered is not for the current fragment
        """

        try:
            while True:
                self.read(frag)
        except XmlReturnError as e:
            if e.tagname != frag.name:
                raise e
        except EOFError:
            pass

    def _search(self, target: str) -> None:
        """Searches for the target character in the XML text

        Args:
            target (str): The character to search for
        """

        while not self._match(target):
            self._skip()

    def read(self, parent: "Optional[XmlFragment]") -> "XmlFragment":
        """Reads an XML fragment

        Args:
            parent (Optional[XmlFragment]): The parent fragment

        Raises:
            ProtocolError: When a protocol related error is encountered
            XmlReturnError: When a closing tag could not find its opening tag

        Returns:
            XmlFragment: The fragment read
        """

        self._skip_whitespace()

        # No tag beginning, read text until tag starts
        if not self._match("<"):
            if parent is None:
                raise ProtocolError("Text is not allowed as root")

            parent.children.append(self._read_text())

        # Check if the tag is the declaration
        if self._match("?"):
            # Skip until the next tag starts
            self._search("<")

        # Read the name of the tag
        name = self._read_name()

        # Check if the tag is a closing tag
        if name.startswith("/"):
            raise XmlReturnError(self._name_split(name[1:])[1])

        # Split the name
        ns, name = self._name_split(name)

        # Create the fragment and add it to the parent
        child = XmlFragment(name, ns)
        if parent is not None:
            parent.children.append(child)

        # Encountered whitespace, read tags
        if self._prev() == " ":
            self._read_props(child)

        match self._prev():
            case "/":
                # Tag is self closing
                if not self._match(">"):
                    raise ProtocolError("No > after / in self closing tag")

            case ">":
                # Tag is not self closing, read children
                self._read_children(child)

            case _:
                raise ProtocolError(f"Not a known character at {self._pos}")

        return child


class XmlFragment:
    @staticmethod
    def stringify(frag: "XmlFragment") -> str:
        """Creates a string representation of the XML fragment

        Args:
            frag (XmlFragment): The XML fragment to stringify

        Returns:
            str: The string representation of the XML fragment
        """

        return "\n".join(
            [
                '<?xml version="1.0" encoding="utf-8" ?>',
                str(frag),
            ]
        )

    def __init__(
        self,
        name: str,
        namespace: Optional[str],
        children: "Optional[list[XmlFragment]]" = None,
    ) -> None:
        self._name: str = name
        self._namespace: Optional[str] = namespace

        self._properties: dict[str, str] = {}
        self._children: list[XmlFragment] = children or []

    @property
    def name(self) -> str:
        """
        Returns:
            str: The name of the fragment
        """

        return self._name

    @property
    def properties(self) -> dict[str, str]:
        """
        Returns:
            dict[str, str]: The properties of the fragment
        """

        return self._properties

    @property
    def children(self) -> "list[XmlFragment]":
        """
        Returns:
            list[XmlFragment]: The children of this fragment
        """

        return self._children

    def __str__(self) -> str:
        """Creates the string representation for this fragment

        Returns:
            str: The string representation of the fragment
        """

        # Open the tag and add the namespace if it exists
        st = ["<"]
        if self._namespace:
            st.append(f"{self._namespace}:")

        # Add the nam
        st.append(self._name)

        # Add all tags
        if len(self.properties) > 0:
            tag_lst = [f'{k}="{v}"' for k, v in self._properties.items()]
            st.append(f" {" ".join(tag_lst)}")

        # Check if the tag has children or can be self closing
        if len(self._children) == 0:
            st.append("/>")
            return "".join(st)

        st.append(">")

        # Add all children
        for c in self._children:
            st.append(str(c))

        # Open the closing tag and add the namespace if it exists
        st.append("</")
        if self._namespace:
            st.append(f"{self._namespace}:")

        # Add the name and return the string
        st.append(f"{self._name}>")

        return "".join(st)


class XmlString(XmlFragment):
    def __init__(self, text: str) -> None:
        super().__init__("str", None)

        self._text = text

    @property
    def text(self) -> str:
        """
        Returns:
            str: The text of this fragment
        """

        return self._text

    def __str__(self) -> str:
        """Creates the string representation for this fragment

        Returns:
            str: The string representation of the fragment
        """

        return self.text
