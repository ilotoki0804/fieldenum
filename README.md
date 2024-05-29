# fieldenum

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
