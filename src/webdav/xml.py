from typing import Optional

from proj_types.proto_error import ProtocolError


class XmlReturnError(Exception):
    def __init__(self, tagname: str) -> None:
        super().__init__()

        self._tagname = tagname

    @property
    def tagname(self) -> str:
        return self._tagname


class XmlReader:
    def __init__(self, text: str) -> None:
        self._text = text.replace("\r", " ").replace("\n", " ")
        self._pos = 0

    def _read(self) -> str:
        self._pos += 1
        if self._pos > len(self._text):
            raise EOFError("End of XML input during READ")

        return self._text[self._pos - 1]

    def _peek(self) -> str:
        if self._pos >= len(self._text) - 1:
            raise EOFError("End of XML input during PEEK")

        return self._text[self._pos]

    def _prev(self) -> str:
        if self._pos <= 0:
            raise EOFError("Beginning of XML input during PREV")

        return self._text[self._pos - 1]

    def _match(self, *expected: str) -> bool:
        if self._peek() in expected:
            self._pos += 1
            return True

        return False

    def _skip_whitespace(self) -> None:
        while self._peek() == " ":
            self._pos += 1

    def _read_text(self) -> "XmlFragment":
        st = []

        while not self._match("<"):
            st.append(self._read())

        return XmlString("".join(st))

    def _read_name(self) -> str:
        st = [self._read()]

        while not self._match(" ", ">", "/"):
            st.append(self._read())

        return "".join(st)

    def _name_split(self, name: str) -> tuple[Optional[str], str]:
        if ":" not in name:
            return (None, name)

        ns, name = name.split(":", 1)
        return (ns, name)

    def _read_tags(self, frag: "XmlFragment") -> None:
        while True:
            prop = []
            in_quotes = False

            while in_quotes or not self._match(" ", "/", ">"):
                c = self._read()

                if c == '"':
                    in_quotes = not in_quotes

                prop.append(c)

            prop = "".join(prop)
            if "=" in prop:
                k, v = prop.split("=", 1)
                frag.tags[k] = v.strip('"')
            else:
                frag.tags[prop] = ""

            if self._prev() in [">", "/"]:
                break

    def _skip(self, amount: int = 1) -> None:
        self._pos += amount

    def _read_children(self, frag: "XmlFragment") -> None:
        try:
            while True:
                self.read(frag)
        except XmlReturnError as e:
            if e.tagname != frag.name:
                raise e
        except EOFError:
            pass

        # frag.update_children()

    def _search(self, target: str) -> None:
        while not self._match(target):
            self._skip()

    def read(self, parent: "Optional[XmlFragment]") -> "XmlFragment":
        self._skip_whitespace()

        # No tag beginning, read text until tag starts
        if not self._match("<"):
            if parent is None:
                raise ProtocolError("Text is not allowed as root")

            parent.children.append(self._read_text())

        if self._match("?"):
            self._search("<")

        name = self._read_name()

        # Closing tag
        if name.startswith("/"):
            raise XmlReturnError(self._name_split(name[1:])[1])

        ns, name = self._name_split(name)

        child = XmlFragment(name, ns)
        if parent is not None:
            parent.children.append(child)

        # Encountered whitespace, read tags
        if self._prev() == " ":
            self._read_tags(child)

        # Tag is self closing
        match self._prev():
            case "/":
                if not self._match(">"):
                    print(self._text[self._pos :])
                    raise ProtocolError("No > after / in self closing tag")
            case ">":
                self._read_children(child)
            case _:
                raise ProtocolError(f"Not a known character at {self._pos}")

        return child


class XmlFragment:
    @staticmethod
    def stringify(frag: "XmlFragment") -> str:
        return "\n".join(
            [
                '<?xml version="1.0" encoding="utf-8" ?>',
                frag._stringify(),
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

        self._tags: dict[str, str] = {}
        self._children: list[XmlFragment] = children or []
        self._parent: Optional[XmlFragment] = None

        self.update_children()

    def update_children(self) -> None:
        for c in self._children:
            c.parent = self

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> "Optional[XmlFragment]":
        return self._parent

    @parent.setter
    def parent(self, val: "XmlFragment") -> None:
        self._parent = val

    @property
    def tags(self) -> dict[str, str]:
        return self._tags

    @property
    def children(self) -> "list[XmlFragment]":
        return self._children

    def __getitem__(self, key: str) -> "XmlFragment":
        for c in self._children:
            if c.name == key:
                return c

        raise ValueError(f"No child with name {key}")

    def __setitem__(self, _: str, val: "XmlFragment") -> None:
        self._children.append(val)

    def _stringify(self) -> str:

        st = ["<"]
        if self._namespace:
            st.append(f"{self._namespace}:")
        st.append(self._name)

        if len(self.tags) > 0:
            tag_lst = [f'{k}="{v}"' for k, v in self._tags.items()]
            st.append(f" {" ".join(tag_lst)}")

        if len(self._children) == 0:
            st.append("/>")
            return "".join(st)

        st.append(">")

        for c in self._children:
            st.append(c._stringify())

        st.append("</")

        if self._namespace:
            st.append(f"{self._namespace}:")
        st.append(f"{self._name}>")

        return "".join(st)


class XmlString(XmlFragment):
    def __init__(self, text: str) -> None:
        super().__init__("str", None)

        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def _stringify(self) -> str:
        return self._text

    def __str__(self) -> str:
        return self.text
