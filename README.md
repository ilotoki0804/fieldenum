# fieldenum

[![PyPI - Downloads](https://img.shields.io/pypi/dm/fieldenum)](https://pypi.org/project/fieldenum/)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Filotoki0804%2Ffieldenum&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://github.com/ilotoki0804/fieldenum)
[![Coverage Status](https://coveralls.io/repos/github/ilotoki0804/fieldenum/badge.svg?branch=master)](https://coveralls.io/github/ilotoki0804/fieldenum?branch=master)
[![Sponsoring](https://img.shields.io/badge/Sponsoring-Toss-blue?logo=GitHub%20Sponsors&logoColor=white)](https://toss.me/ilotoki)

Rust-like fielded Enums in Python

**[한국어로 보기](docs/README-ko.md)**

## Examples

```python
from fieldenum import fieldenum, Unit, Variant

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)

# Corresponding code in Rust:
# enum Message {
#     Quit,
#     Move { x: i32, y: i32 },
#     Write(String),
#     ChangeColor(i32, i32, i32),
# }


# usage
message = Message.Quit
message = Message.Move(x=1, y=2)
message = Message.Write("hello, world!")
message = Message.ChangeColor(256, 256, 0)
```

## Credits

This project is heavily influenced by [Rust's `Enum`](https://doc.rust-lang.org/reference/items/enumerations.html), and also borrows some of its design from [rust_enum](https://github.com/girvel/rust_enum).

## Releases

* 0.1.0: initial release
