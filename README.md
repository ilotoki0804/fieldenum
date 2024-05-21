# fieldenum

Rust-like fielded Enum in Python

## Examples

```python
from fieldenum import fieldenum, Item

# define
@fieldenum
class Message:
    Quit = Item()
    Move = Item(x=int, y=int)
    Write = Item(str)
    ChangeColor = Item(int, int, int)

# Corresponding code in Rust:
# enum Message {
#     Quit,
#     Move { x: i32, y: i32 },
#     Write(String),
#     ChangeColor(i32, i32, i32),
# }


# usage
message = Message.Quit()
message = Message.Move(x=1, y=2)
message = Message.Write("hello, world!")
message = Message.ChangeColor(256, 256, 0)
```

## Credits

This project is heavily influenced by [Rust's `Enum`](https://doc.rust-lang.org/reference/items/enumerations.html), and also borrows some of its design from [rust_enum](https://github.com/girvel/rust_enum).
