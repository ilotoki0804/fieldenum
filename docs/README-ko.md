# fieldenum

파이썬에서의 러스트 스타일의 필드형 enum

**[English Docs](/README.md)**

## Introduction

러스트의 여러 킬러 기능 중에서도 단연 가장 돋보이는 것은 enum입니다.
함수형 프로그래밍의 개념을 차용한 이 enum은 매우 강력한데,
그중에서도 돋보이는 점은 바로 필드를 가질 수 있다는 점입니다.

파이썬에도 이미 `enum`이라는 기본 모듈이 있으나, 이는 필드를 사용할 수가 없습니다.
반대로 `dataclass`도 기본적으로 지원되나, 이는 enum처럼 선택지의 개념이 존재하지 않습니다.

fieldenum은 러스트와 거의 비슷하면서도 파이썬의 문법과 잘 어울리는 필드가 있는 enum을 사용할 수 있도록 합니다.
또한 이를 통해 Railroad Oriented Programming이나 `Option`과 같은 여러 함수형 프로그래밍의 개념을 활용할 수 있게 됩니다.

## Installation

다음의 명령어를 통해 `fieldenum`을 설치할 수 있습니다.

```python
pip install fieldenum
```

메인 파트는 파이썬 3.10 이상에서 호환됩니다. 다만, 하위 모듈인 `fieldenum.enums`는 파이썬 3.12 이상에서만 사용 가능합니다.

## 사용 방법

### `@fieldenum`

클래스에 `Variant`혹은 `Unit`을 값으로 가지는 변수들을 추가하고 클래스를 `@fieldenum`으로 감싸주면 fieldenum이 됩니다.
예를 들어 다음과 같이 코드를 짤 수 있습니다.

```python
from fieldenum import Variant, Unit, fieldenum

@fieldenum  # fieldenum으로 감싸면 만들어집니다. 깜박하고 안 쓰면 안 됩니다!
class Message:
    Quit = Unit  # 유닛 배리언트는 다음과 같이 정의합니다.
    Write = Variant(str)  # 튜플 배리언트는 다음과 같이 정의합니다.
```

### 배리언트 정의하기

모든 fieldenum은 배리언트를 가지는데, 이 베리언트들은 enum이 가질 수 있는 상태들의 모음입니다.

fieldenum이 만들어지면 원래의 enum 클래스는 더 이상 인스턴스화될 수 없고,
그 대신 각각의 배리언트들이 인스턴스화될 수 있습니다.

또한 enum은 상속될 수 없기 때문에 모든 enum 클래스의 서브클래스는 배리언트밖에 없고,
enum 클래스의 인스턴스에는 배리언트들의 인스턴스만 존재합니다.

### 유닛 배리언트

유닛 배리언트는 별도의 필드를 갖지 않는 배리언트로, 괄호를 통해 값을 초가화할 필요가 없습니다.

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Message:
    # 유닛 배리언트는 다음과 같이 정의합니다.
    Quit = Unit
    Stay = Unit

message: Message = Message.Quit

# message가 Message.Quit인지 확인합니다.
if message is Message.Quit:
    print("Quit!")

# match statement를 사용할 수도 있습니다.
match message:
    case Message.Quit:
        print("Quit!")

    case Message.Stay:
        print("Stay!")
```

### 튜플형 배리언트

튜플형 배리언트는 튜플형의 익명의 값을 가지는 배리언트입니다.

튜플형 배리언트는 다음과 같이 정의합니다.

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Message[T]:
    Quit = Variant(int)  # Variant(...)와 같이 적고 안에는 타입을 적습니다.
    Stay = Variant(T)  # 제너릭도 사용 가능합니다.
    Var3 = Variant(int, str, dict[int, str])  # 여러 값을 이어서 적으면 각각이 파라미터가 됩니다.


Message.Quit(123)  # OK
Message.Stay[str]("hello")  # OK
Message.Stay("hello")  # OK
Message.Var3(123, "hello", {1: "world"})  # OK
```

튜플의 값에는 타입이 적히는데, 이는 런타임에 확인되지는 않는 어노테이션에 가깝습니다.

그러나 값이 확인되는 것을 원한다면, `runtime_check`를 `True`로 하세요.

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum(runtime_check=True)  # 런타입 체크를 켭니다.
class Message[T]:
    # 일반 타입은 `isinstance()`를 통해 확인됩니다.
    Quit = Variant(int)
    # 제너릭은 검사되지 않습니다.
    Stay = Variant(T)
    # 각각의 파라미터에 타입을 체크합니다.
    # 이때 Union (이 경우 `str | int`)는 체크되지만
    # generic alias (이 경우`dict[int, str]`)는 체크되지 않습니다.
    Var3 = Variant(int, str | int, dict[int, str])

Message.Quit(123)  # 오류 없음
Message.Quit("invalid")  # TypeError (타입 오류)
Message.Stay("hello")  # 오류 없음
Message.Stay(1234)  # 잘못됐지만 오류 없음 (제너릭)
Message.Var3(123, "hello", {1: "world"})  # 오류 없음
Message.Var3(123, 123, {1: "world"})  # 오류 없음
Message.Stay(123, 123.456, {1: "world"})  # TypeError (Union 타입 오류)
Message.Var3(123, "hello", {"hello": "world"})  # 잘못됐지만 오류 없음 (제너릭 alias)
Message.Var3(123, "hello", 123)  # 잘못됐지만 오류 없음 (제너릭 alias)
```

### 이름 있는 배리언트

이름 있는 배리언트는 순서가 없는 여러 키워드로 이루어진 배리언트입니다.

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Cord[T]:
    D1 = Variant(x=float)
    D2 = Variant(x=float, y=float)
    D3 = Variant(x=float, y=float, z=float)
    D4 = Variant(timestamp=float, x=float, y=float, z=float)


Cord.D1(x=123.456)
Cord.D3(x=1343.5, y=25.2, z=465.312)
```

이때 위치 인자를 사용해 초기화할 수는 없습니다.

```python
Cord.D1(123.456)  # XXX: 불가능
```

값은 attribute를 통해서도 접근할 수 있습니다.

```python
cord = Cord.D3(x=1343.5, y=25.2, z=465.312)

assert cord.x == 1343.5
assert cord.y == 25.2
assert cord.x == 465.312
```

물론 match문을 사용하는 방식도 있으며, 일반적으로는 속성으로 접근하는 방식보다 더 선호됩니다.

```python
match cord:
    case Cord.D1(x=x):
        print(f"x cord is ({x})")

    case Cord.D2(x=x, y=y):
        print(f"x-y cord is ({x}, {y})")

    case Cord.D3(x=x, y=y, z=_):
        print(f"x-y cord is ({x}, {y})")

    case Cord.D3(timestamp=time, x=x, y=y, z=_):
        print(f"x-y cord is ({x}, {y}) at {time}")
```

런타임 체크의 규칙은 튜플형과 같습니다.

### match문을 이용한 enum의 사용

`enum`은 파이썬 3.10에서 추가된 match문과 같이 사용하면 매우 어울립니다.
다음과 같은 enum이 있다고 해봅시다.

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
```

이때 이 enum을 처리하는 함수는 다음과 같이 작성할 수 있습니다.

```python
class MyClass:
    def process_message(self, message: Message):
        match message:
            case Message.Quit:
                sys.exit(0)

            case Message.Move(x=x, y=y):
                self.x += x
                self.y += y

            case Message.Write(value):
                self.f.write(value)

            case Message.ChangeColor(red, green, blue):
                self.color = rgb_to_hsv(red, green, blue)
```

match문에 대한 자세한 설명은 [공식 match문 튜토리얼](https://docs.python.org/3/tutorial/controlflow.html#match-statements)을 참고하세요.

### 원본 클래스의 메서드 사용

enum을 만들면 그 배리언트들은 원본 클래스의 메서드들을 사용할 수 있습니다.
예를 들어 다음은 `Option`의 구현을 모사해 나타낸 예시입니다.

```python
from fieldenum import fieldenum, Variant

@fieldenum
class Option[T]:
    Nothing = Unit
    Some = Variant(T)

    def unwrap(self) -> T:
        match self:
            case Option.Nothing:
                print("Unwrap failed.")

            case Option.Some(value):
                return value
```

`Option`에 구현되어 있는 메서드는 옵션의 배리언트들인 `Nothing`이나 `Some`에서 사용될 수 있습니다.

```python
Option.Nothing.unwrap()  # TypeError를 raise합니다.
print(Option.Some(123).unwrap())  # 123을 출력합니다.
```

## `isinstance()`

모든 배리언트는 원본 enum 클래스의 인스턴스입니다. 따라서 `isinstance(message, Message)`와 같이 `isinstance()`를 통해 해당 enum인지를 쉽게 확인할 수 있습니다.

```python
from fieldenum import fieldenum, Variant

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)

assert isinstance(Message.Write("hello!"), Message)
```

## Examples

## `Option`

`Option` 타입은 값이 있거나 없을 수 있는 아주 흔한 상황을 나타냅니다.

파이썬 개발자들은 이런 상황을 위해 `Optional[T]`이나 `T | None`을 사용합니다.
예를 들어 `Optional[str]`나 `str | None`이라고 적죠.

`fieldenum.enums` 패키지에서 제공되는 `Option`은 `Optional`과 정말 비슷합니다. `Option[str]`은 `Optional[str]`과 같이
값이 없거나 `str`이죠.

하지만 여러 면에서 `Option`은 독특한 장점을 가집니다.

다음의 예시를 살펴보세요.

```python
from fieldenum.enums import Option, Some

optional: str | None = input("Type anything!") or None
option = Option.new(input("Type anything!") or None)

# Union을 사용한 경우 다음과 같은 코드는 타입 체커 오류를 일으키고, 런타임 오류의 가능성이 있습니다.
print(optional.upper())  # 어쩔 때는 오류가 나고 어쩔 때는 아닙니다.

# 이렇게 사용하는 것은 아예 불가능하고, 이는 런타임에서도 명백합니다.
print(option.upper())  # 항상 오류가 발생합니다.

# 그 대신, 사용자는 다음과 같이 명시적으로 값을 변환시켜야 합니다.
match option:
    case Some(value):
        print(value.upper())

    case Option.Nothing:
        print("Nothing to show.")

print(option.unwrap("Nothing to show."))  # 위에 있던 코드와 완전히 같은 코드입니다.
```

`Option`의 장점 중 하나는 `Union`인 `Optional`아니 `str | None`과 달리 `Option`이 '실제 클래스'라는 점입니다.
따라서 실제 메소드들을 구현할 수 있습니다.

예를 들어 위에서 보여드린 `.unwrap()` 메소드도 있고 그 외에도 `.map()` `.new()` 등의 함수도 존재합니다.
또한 `bool()`같은 속성도 안정적으로 구현할 수 있습니다.
예를 들어 `int | None` 타입의 경우 값이 `None`일 때도 거짓으로 처리되지만, `0`일 때도 거짓이어서 참인지 거짓인지를 통해 `None`인지 `int`인지 구별하기 애매합니다.

하지만 `Option`의 경우에는 안정적으로 `Nothing`일 때는 거짓, `Some`일 때는 참으로 처리할 수 있습니다.
예를 들어 나음의 코드는 항상 `0`을 출력합니다.

```python
from fieldenum.enums import Option, Some

int_option = Option.Some(0)
if int_option:  # evaluated as `True`
    print(int_option)
else:
    print("There's no value!")
```

`.new()`는 `Optional`을 `Option`으로 바꿔줍니다. 더 쉽게 말하면, `Option.new(None)`은 `Option.Nothing`을 반환하고, 다머지 경우에서는 `Option.new(value)`는 `Option.Some(value)`를 반환합니다.

`.map(func)`는 `Option.Nothing`에서는 별 영향이 없고, `Option.Some(value)`에서는 `func(value)` 값을 `Option.new`안에 넣습니다.
예를 들어 `Option.Nothing.map(str)`의 결과는 그대로 `Option.Nothing`이지만, `Option.Some(123).map(str)`의 결과는 `Option.Some('123')`입니다.

이러한 기능들은 [PEP 505](https://peps.python.org/pep-0505/)의 부분적인 대안이 될 수 있습니다.

### `Message` enum의 예시

```python
from fieldenum import fieldenum, Variant, Unit

# define
@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)


# usage
message = Message.Quit
message = Message.Move(x=1, y=2)
message = Message.Write("hello, world!")
message = Message.ChangeColor(256, 256, 0)
```

### 실제 사례: `ConcatOption`

fieldenum는 이질적인 성격을 가진 설정들을 모아놓는 경우에 사용하기에 좋았습니다.
제가 fieldenum을 만들게 된 직접적인 계기이기도 합니다.

아래의 예시는 이미지가 여럿 들어 있는 디렉토리의 이미지들을 특정 기준을 통해
이미지들을 세로로 결합시키는 기능을 가진 패키지에서 사용될 수 있는
fieldenum의 예시입니다.

각각의 요구사항에 따라 필요한 정보와 타입이 다르기에 키워드 인자 등으로 해결하기 매우 곤란합니다.
fieldenum을 사용하면 문제를 우아하게 해결할 수 있습니다.

```python
from fieldenum import fieldenum, Variant, Unit

@fieldenum
class ConcatOption:
    """이미지를 결합하는 기준을 설정합니다."""
    All = Unit  # 모든 이미지를 결합합니다.
    Count = Variant(int)  # 이미지를 설정된 개수만큼 결합합니다.
    Height = Variant(int)  # 이미지의 세로 픽셀 수가 설정한 수 이상이 되도록 결합합니다.
    Ratio = Variant(float)  # 이미지의 세로 픽셀 대 가로 픽셀 수 비 이상이 되도록 결합합니다.

def concatenate(directory: Path, option: ConcatOption):
    ...

# 사용 예시들
concatenate(Path("images/"), ConcatOption.All)
concatenate(Path("images/"), ConcatOption.Count(5))
concatenate(Path("images/"), ConcatOption.Height(3000))
concatenate(Path("images/"), ConcatOption.Ratio(11.5))
```

### 연결 리스트 예시

다음은 [Rust By Example](https://doc.rust-lang.org/rust-by-example/custom_types/enum/testcase_linked_list.html)에서 찾을 수 있는 연결 리스트 구현 예시입니다.

```rust
// 러스트에 대해 잘 모르신다면 이 원본 러스트 구현은 넘겨뛰고
// 아래에 있는 fieldenum 구현을 확인해 보세요!

use crate::List::*;

enum List {
    Cons(u32, Box<List>),
    Nil,
}

impl List {
    fn new() -> List {
        Nil
    }

    fn prepend(self, elem: u32) -> List {
        Cons(elem, Box::new(self))
    }

    fn len(&self) -> u32 {
        match *self {
            Cons(_, ref tail) => 1 + tail.len(),
            Nil => 0
        }
    }

    fn stringify(&self) -> String {
        match *self {
            Cons(head, ref tail) => {
                format!("{}, {}", head, tail.stringify())
            },
            Nil => {
                format!("Nil")
            },
        }
    }
}

fn main() {
    let mut list = List::new();

    list = list.prepend(1);
    list = list.prepend(2);
    list = list.prepend(3);

    println!("linked list has length: {}", list.len());
    println!("{}", list.stringify());
}
```

위의 러스트 코드는 아래와 같은 파이썬 코드로 변환할 수 있습니다.

```python
from __future__ import annotations

from fieldenum import Unit, Variant, fieldenum, unreachable


@fieldenum
class List:
    Cons = Variant(int, "List")
    Nil = Unit

    @classmethod
    def new(cls) -> List:
        return List.Nil

    def prepend(self, elem: int) -> List:
        return List.Cons(elem, self)

    def __len__(self) -> int:
        match self:
            case List.Cons(_, tail):
                return 1 + len(tail)

            case List.Nil:
                return 0

            case other:
                unreachable(other)

    def __str__(self) -> str:
        match self:
            case List.Cons(head, tail):
                return f"{head}, {tail}"

            case List.Nil:
                return "Nil"

            case other:
                unreachable(other)


if __name__ == "__main__":
    linked_list = List.new()
    linked_list = linked_list.prepend(1)
    linked_list = linked_list.prepend(2)
    linked_list = linked_list.prepend(3)
    print("length:", len(linked_list))  # length: 3
    print(linked_list)  # 3, 2, 1, Nil
```

## Railroad Oriented Programming

fieldenum에서 사용 가능한 예외의 대안인 Railroad Oriented Programming의 자세한 설명을 보고 싶다면 [BoundResult를 통한 ROP](railroad-oriented-ko.ipynb)을 확인하세요.

## fieldenum 튜토리얼

> 이 파트의 대부분은 [<러스트 프로그래밍 언어>의 '열거형 정의하기' 쳅터](https://doc.rust-kr.org/ch06-01-defining-an-enum.html) 내용을 fieldenum의 경우에 맞게 변경한 것입니다.

fieldenum(이하 enum과 혼용)은 어떤 값이 여러 개의 가능한
값의 집합 중 하나라는 것을 나타내는 방법을 제공합니다. 예를 들면 `Rectangle`이
`Circle`과 `Triangle`을 포함하는 다양한 모양들의 집합 중 하나라고 표현하고
싶을 수도 있습니다. 이렇게 하기 위해서 enum은 가능한 것들을 나타내게 해줍니다.

IP 주소를 다루는 프로그램을 만들어 보면서,
어떤 상황에서 enum이 유용하고 적절한지 알아보겠습니다.
현재 사용되는 IP 주소 표준은 IPv4, IPv6 두 종류입니다(앞으로 v4, v6로 표기하겠습니다).
우리가 만들 프로그램에서 다룰 IP 종류는 이 두 가지가 전부이므로,
이처럼 가능한 모든 배리언트 들을 죽 *늘어놓을* 수 있는데, 이 때문에
`enum`이라는 이름이 붙은 것입니다.

IP 주소는 반드시 v4나 v6 중 하나만 될 수 있는데,
이러한 특성은 enum 자료 구조에 적합합니다.
왜냐하면, enum의 값은 여러 배리언트 중 하나만 될 수 있기 때문입니다.
v4, v6는 근본적으로 IP 주소이기 때문에, 이 둘은 코드에서
모든 종류의 IP 주소에 적용되는 상황을 다룰 때 동일한 타입으로 처리되는 것이
좋습니다.

`IpAddrKind`라는 enum을 정의하면서 포함할 수 있는 IP 주소인 `V4`와 `V6`를
나열함으로써 이 개념을 코드에 표현할 수 있습니다.
이것들을 enum의 *배리언트*라고 합니다:

```python
from fieldenum import Unit, Variant, fieldenum, unreachable

@fieldenum
class IpAddrKind:
    V4 = Unit
    V6 = Unit
```

### enum 값

아래처럼 `IpAddrKind`의 두 개의 배리언트에 대한 변수를 만들 수 있습니다:

```python
four = IpAddrKind.V4
six = IpAddrKind.V6
```

이제 `IpAddrKind` 타입을 인수로 받는 함수를 정의해 봅시다:

```python
def route(ip_kind: IpAddrKind):
    pass
```

그리고, 배리언트 중 하나를 사용해서 함수를 호출할 수 있습니다:

```python
route(IpAddrKind.V4)
route(IpAddrKind.V6)
```

enum을 사용하면 더 많은 이점이 있습니다. IP 주소 타입에 대해
더 생각해 보면, 지금으로서는 실제 IP 주소 *데이터*를 저장할
방법이 없고 어떤 *종류*인지만 알 수 있습니다. 이 문제를 dataclass를 사용하여 해결하고
싶을 수 있겠습니다:

```python
from dataclasses import dataclass

from fieldenum import Unit, Variant, fieldenum, unreachable

@fieldenum
class IpAddrKind:
    V4 = Unit
    V6 = Unit

@dataclass
class IpAddr:
    kind: IpAddrKind
    address: str

home = IpAddr(kind=IpAddrKind.V4, address="127.0.0.1")
loopback = IpAddr(kind=IpAddrKind.V6, address="::1")
```

<span class="caption">`dataclass`를 사용해서 IP 주소의 데이터와
`IpAddrKind` 배리언트 저장하기</span>

여기서는 `IpAddrKind` 타입인 `kind` 키와
`str` 타입인 `address` 키를 갖는 `IpAddr`를 정의했습니다.
그리고 이 dataclass를 가지는 두 변수를 생성했습니다. 첫 번째 `home`은
`kind`의 값으로 `IpAddrKind.V4`를, 연관된 주소 데이터로
`127.0.0.1`을 갖습니다. 두 번째 `loopback`은 `IpAddrKind`의 다른 배리언트인
`V6`를 값으로 갖고, 연관된 주소로 `::1`을 갖습니다. `kind`와 `address`의
값을 함께 사용하기 위해 dataclass를 사용했습니다. 그렇게 함으로써 배리언트가
연관된 값을 갖게 되었습니다.

각 배리언트에 필드를 추가하는 방식을 사용해서 enum을 dataclass의 일부로
사용하는 방식보다 더 간결하게 동일한 개념을 표현할 수 있습니다.
`IpAddr` enum의 새로운 정의에서 두 개의 `V4`와 `V6` 배리언트는 연관된
`str` 타입의 값을 갖게 됩니다:

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class IpAddr:
    V4 = Variant(str)
    V6 = Variant(str)

home = IpAddr.V4("127.0.0.1")
loopback = IpAddr.V6("::1")
```

enum의 각 배리언트에 직접 데이터를 붙임으로써, dataclass를 사용할 필요가
없어졌습니다. 또한 여기서 enum의 동작에 대한 다른 세부 사항을 살펴보기가
좀 더 쉬워졌습니다: 각 enum 배리언트의 이름이 해당 enum 인스턴스의
생성자 함수처럼 된다는 것이죠. 즉, `IpAddr.V4()`는 `str` 인수를
입력받아서 `IpAddr` 타입의 인스턴스 결과를 만드는 함수입니다.
enum을 정의한 결과로써 이러한 생성자 함수가 자동적으로
정의됩니다.

dataclass 대신 enum을 사용하면 또 다른 장점이 있습니다.
각 배리언트는 다른 타입과 다른 양의 연관된 데이터를 가질 수 있습니다.
V4 IP 주소는 항상 0 ~ 255 사이의 숫자 4개로 된 구성 요소를 갖게 될 것입니다.
`V4` 주소에 4개의 `int` 값을 저장하길 원하지만, `V6` 주소는 하나의 `str`
값으로 표현되길 원한다면, dataclass로는 이렇게 할 수 없습니다.
fieldenum은 이런 경우를 쉽게 처리합니다:

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class IpAddrKind:
    V4 = Variant(int, int, int, int)
    V6 = Variant(str)

home = IpAddrKind.V4(127, 0, 0, 1)
loopback = IpAddrKind.V6("::1")
```

enum 배리언트에는 어떤 종류의 데이터라도 넣을 수 있습니다.
문자열, 숫자 타입, dataclass 등은 물론, 다른 enum마저도 포함할 수 있죠!

enum의 다른 예제를 살펴봅시다. 이 예제에서는 각 배리언트에
다양한 종류의 타입들이 포함되어 있습니다:

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
```

<span class="caption">`Message` enum은 각 배리언트가 다른 타입과
다른 양의 값을 저장합니다.</span>

이 enum에는 다른 데이터 타입을 갖는 네 개의 배리언트가 있습니다:

* `Quit`은 연관된 데이터가 전혀 없습니다.
* `Move`은 dataclass처럼 이름이 있는 필드를 갖습니다.
* `Write`은 하나의 `str`을 가집니다.
* `ChangeColor`는 세 개의 `int`를 가집니다.

fieldenum에 추가적인 메소드를 정의할 수 있습니다. 여기 `Message` fieldenum에
정의한 `call`이라는 메서드가 있습니다:

```python
from fieldenum import Variant, Unit, fieldenum, unreachable

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)

    def process(self):
        print(f"Processing `{self}`...")

m = Message.Write("hello")
m.process()  # Processing `Message.Write("hello")`...
```

메서드 본문에서는 `self`를 사용하여 호출한 fieldenum의 값을 가져올 것입니다.
이 예제에서 생성한 변수 `m`은  `Message.Write("hello")` 값을 갖게 되고,
이 값은 `m.process()`이 실행될 때
`process` 메서드 안에서 `self`가 될 것입니다.

## 안티 패턴

<!-- ### 배리언트 자체를 타입으로 사용하는 것

하나의 배리언트의 값을 내보내고 싶을 때 다음과 같이 배리언트를 타입으로 처리하고 싶을 수 있습니다.

```python
from fieldenum import fieldenum, Variant, Unit
from fieldenum.enums import Option

def hello() -> Option.Some:  # XXX
    return Option.Some("hello")

def print_hello(option: Option.Some):  # XXX
    print(option.unwrap())

value = hello()
print_hello(value)
```

그 대신 함수는 `Option`을 값으로 넘겨 해당 값의 사용자가 처리하도록 해야 합니다.

```python
from fieldenum import fieldenum, Variant, Unit, unreachable
from fieldenum.enums import Option

def hello() -> Option:  # GOOD
    return Option.Some("hello")

def print_hello(option: Option):  # GOOD
    print(option.unwrap())

value = hello()
print_hello(value)
```

마찬가지로 여러 배리언트를 Union으로 묶어 (예: `Option.Nothing | Option.Some`) 사용하는 것도 피해야 합니다.

명백하게 이득이 되는 것이 아니라면 이러한 방식으로 사용하는 것을 자제해 주세요. -->

### 필드의 타입으로 Union을 사용하는 것

다음과 같이 배리언트의 필드에 Union을 사용하는 것은 금지되지는 않지만 말리고 싶습니다.
그 대신 두 개의 다른 배리언트로 나누는 것을 고려해 보세요.

```python
from fieldenum import fieldenum, Variant, Unit, unreachable

@fieldenum
class InvalidIoResult:
    Success = Variant(content=str)
    Error = Variant(str | int)  # XXX

# Do instead:
@fieldenum
class ValidIoResult:
    Success = Variant(content=str)
    ErrorCode = Variant(int)
    ErrorMessage = Variant(str)
```

## 디자인

### 상속 금지

러스트의 enum이 그렇듯 fieldenum 또한 상속이 가능하지 않습니다. 이는 런타임에서도 저지됩니다.

이는 메서드를 그대로 사용할 수 있다는 상속의 가장 큰 이유가 fieldenum에게는 무의미하고,
상속의 특성이 fieldenum에서 해롭게 작용하기 때문입니다.

예를 들어 봅시다. 만약 모종의 사유로 `Option` 배리언트에 `Maybe`를 추가하고 싶다고 해 봅시다.

```python
from fieldenum import fieldenum, Variant, Unit

@fieldenum
class Option[T]:
    """실제 Option 구현의 단순화 버전"""

    Nothing = Unit
    Some = Variant(T)

    def unwrap(self) -> T:
        """실제 `unwrap` 구현을 단순화한 버전"""
        match self:
            case Option.Nothing:
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    ...

@fieldenum
class MaybeOption[T](Option[T]):  # XXX
    Maybe = Unit
```

이렇게 하면 문제가 생깁니다. 바로 `Option`에서 사용되었던 기존의 모든 메서드가 망가진다는 점입니다.

예를 들어 `Maybe` 배리언트에서 `unwrap`을 사용하면 `Unreachable` 오류가 나게 됩니다.

```python
MaybeOption.Maybe.unwrap()  # Unreachable
```

`Unreachable` 오류는 코드에 버그가 있을 때 생기는 오류인데, 이 경우에는 버그가 아니니 `Maybe`가 처리되도록
메서드를 직접 변경해야 합니다.

```python
@fieldenum
class MaybeOption[T](Option[T]):  # XXX
    Maybe = Unit

    def unwrap(self) -> T:
        """실제 `unwrap` 구현을 단순화한 버전"""
        match self:
            case Option.Nothing:
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Some(value):
                return value

            case MaybeOption.Maybe:  # 메서드 변경
                return None

            case other:
                unreachable(other)
```

그러나 이 방식의 문제는 모든 메서드에 대해 이러한 작업을 수행해야 한다는 점이고,
그 말은 상속을 써야 하는 근본적인 이유가 없어진다는 의미입니다.

따라서 그 대신 다음과 같은 완전히 다른 enum을 작성하는 것이 더 적절합니다.

```python
@fieldenum
class MaybeOption[T]:
    Nothing = Unit
    Some = Variant(T)
    Maybe = Unit

    def unwrap(self) -> T:
        match self:
            case Option.Nothing:
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Some(value):
                return value

            case MaybeOption.Maybe:
                return None

            case other:
                unreachable(other)
```

물론 새로운 배리언트를 추가하는 것인 아닌 새로운 메서드를 추가하기 위해
상속을 고려해 볼 수도 있습니다.

하지만 구현상의 이유로 그 메서드는 사용할 수 없기 때문에 사실상 무의미합니다.

```python
from fieldenum import fieldenum, Variant, Unit
from fieldenum.enums import Option

@fieldenum
class DebuggableOption[T](Option[T]):
    def debug(self):
        match self:
            case DebuggableOption.Nothing:
                print("Nothing here...")

            case DebuggableOption.Some(value):
                print(f"here is {value}!")

# 마치 작동하는 것처럼 보입니다.
opt = DebuggableOption.Some(123)
# AttributeError가 raise됩니다. 실제로는 debug라는 메서드는 존재하지 않기 때문입니다.
opt.debug()
# 왜냐하면 `opt`은 `DebuggableOption`의 인스턴스가 아니기 때문입니다!
assert not isinstance(opt, DebuggableOption)
# 그 대신 `opt`는 `Option`의 인스턴스입니다(정확히는 `Option`의 서브클래스(Option의 배리언트)의 인스턴스입니다).
assert isinstance(opt, Option)
```

구현을 변경하면 서브클래싱이 가능하게 할 수도 있습니다.
그러나 이는 fieldenum에 대한 근본적인 가정을 흐트러뜨립니다.

예를 들어 매우 전형적인 `append_option`이라는 함수를 정의해 봅시다.

```python
from collections.abc import MutableSequence

from fieldenum import fieldenum, Variant, Unit
from fieldenum.enums import Option, Some

def append_option(sequence: MutableSequence, option: Option):
    # 이 단언문을 통해 타입 힌트를 위반한 코드가 걸러집니다.
    assert isinstance(option, Option)

    # 설명을 위한 예시입니다. 실제로는
    # myoption.map(mylist.append)를 사용하면 됩니다!
    match option:
        # option은 Option.Nothing | Option.Some으로 볼 수 있습니다.
        case Option.Some(value):
            sequence.append(value)

        case Option.Nothing:
            pass

        # 이 코드를 통해 프로그램에 '명백한 오류'가 있을 시
        # 빠르게 잡아낼 수 있습니다.
        case other:
            unreachable(other)


mylist = []
append_option(mylist, Some(1))  # 1이 append됩니다.
assert mylist == [1]
append_option(mylist, Some(2))  # 2가 append됩니다.
assert mylist == [1, 2]
append_option(mylist, Option.Nothing)  # 아무것도 append되지 않습니다.
assert mylist == [1, 2]
```

만약 서브클래싱을 허용한다면 위의 코드는 완전히 무너지게 됩니다.

```python
append_option(mylist, DebuggableOption.Some(1))  # Unreachable
```

위의 코드를 실행하면 `DebuggableOption.Some(1)`는 `Option`의 서브클래스이지만,
동시에 `Option.Some`도, `Option.Nothing`도 아니기에 `Unreachable` 오류를 발생시키게 됩니다.

이는 타입 체커에게조차도 완전히 유효한 코드이기 때문에 잡아내기 쉽지 않으며,
fieldenum을 사용하는 근본적인 목적을 흐리기 때문에 금지됩니다.

#### 영향

enum은 모두 서브클래싱이 불가능하기에 다음과 같이 `cls`나 `type(self)`를 사용하는 대신
그냥 `Option`과 같이 이름을 직접 사용해도 좋습니다.

```python
@fieldenum
class Option[T]:
    Nothing = Unit
    Some = Variant(T)

    @classmethod
    def new(cls, value: T | None) -> Self:
        """실제 `Option.new()`의 구현의 단순화 버전"""
        match value:
            case None:
                return Option.Nothing  # cls.Nothing이 아닌 Option.Nothing을 사용했습니다.

            case value:
                return Option.Some(value)  # 여기도 cls.Some(value)이 아닌 Option.Some(value)입니다.

    def unwrap(self) -> T:
        """실제 `unwrap` 구현을 단순화한 버전"""
        match self:
            case Option.Nothing:  # type(self) 대신 Option을 그대로 사용해도 됩니다.
                raise UnwrapFailedError("Unwrap failed.")

            case Option.Some(value):
                return value

            case other:
                unreachable(other)

    ...
```

### 왜 타입을 타입 파라미터 대신 호출 인자로 받나요?

fieldenum의 배리언트는 타입을 타입 파라미터가 아닌 호출 인자로 받습니다.

```python
from fieldenum import fieldenum, Variant, Unit

@fieldenum
class InvalidMessage:  # XXX
    Quit: Unit  # XXX
    Move = Variant[x=int, y=int]  # XXX
    Write: Variant[str]  # XXX
    ChangeColor: Variant[int, int, int]  # XXX


@fieldenum
class ValidMessage:  # GOOD
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
```

해당 결정에는 두 가지 이유가 있습니다.

* 러스트 코드의 모양새를 최대한 따라가고자 했습니다. 타입 파라미터는 러스트의 모양새와는 다릅니다.
* 튜플 배리언트는 어느 정도 구현이 가능하지만, 이름 있는 필드에 대해서는 아예 표현이 불가능합니다. 예를 들어 `Variant[x=int, y=int]`는 `SyntaxError`가 나는 컴파일 불가능한 틀린 문법입니다.

### 왜 러스트의 named field와 비슷하게 생긴 딕셔너리 대신 keyword arguments를 사용하나요?

이름 있는 배리언트는 고정적입니다. 이러한 고정적인 값에는 딕셔너리보다 keyword arguments가 더 유용하고 어울립니다.

또한 딕셔너리를 사용하지 않음으로써 match문의 가독성이 높아집니다.

### 왜 `__init__`을 추가할 수 없나요?

`__init__`은 기본적으로 객체가 생성됨을 전제로 합니다. enum 클래스의 서브클래스는 *enum 클래스 자기 자신을 포함해서* 절대 배리언트가 아니면 안 되기에 `__init__`은 기본적으로 사용이 금지되어 있습니다.

이는 만약 사용자가 `__init__`을 추가로 명시해 사용하더라도 마찬가지입니다.

### 대략적인 실제 구현 모사

다음과 같은 enum이 있다고 해 봅시다.

```python
from fieldenum import fieldenum, Variant

@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)

    def say_loud(self):
        if self is not Message.Quit:
            print(self)
```

위의 fieldenum은 아래의 코드와 유사합니다:

```python
class Message:
    def say_loud(self):
        if self is not Message.Quit:
            print(self)

QuitMessage = Message()
class MoveMessage(Message):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
class WriteMessage(Message):
    def __init__(self, _0: str, /):
        self._0 = _0
class ChangeColorMessage(Message):
    def __init__(self, _0: int, _1: int, _2: int, /):
        self._0 = _0
        self._1 = _1
        self._2 = _2

Message.Quit = QuitMessage
Message.Move = MoveMessage
Message.Write = WriteMessage
Message.ChangeColor = ChangeColorMessage
```

## Unit 배리언트 vs fieldless 배리언트

필드가 없는 값을 다룰 때는 두 가지 배리언트를 사용 가능합니다.
첫 번째는 유닛 배리언트로, `()`를 통해 인스턴스화할 필요가 없이 바로 사용 가능한 배리언트입니다.
두 번째는 fieldless 배리언트로, `()`를 통해 인스턴스화가 필요하지만, 그 안에는 어떠한 인자도 받지 않습니다.

```python
from fieldenum import fieldenum, Variant, Unit

@fieldenum
class NoFieldVariants:
    UnitVariant = Unit
    FieldlessVariant = Variant()

unit = NoFieldVariants.UnitVariant  # 괄호를 필요로 하지 않습니다.
fieldless = NoFieldVariants.FieldlessVariant()  # 괄호를 필요로 합니다.

# 두 배리언트 모두 isinstance로 확인할 수 있습니다.
assert isinstance(unit, NoFieldVariants)
assert isinstance(fieldless, NoFieldVariants)

# 두 배리언트 모두 싱글톤이기에 `is` 연산자로 동일성을 확인할 수 있습니다.
assert unit is NoFieldVariants.UnitVariant
assert fieldless is NoFieldVariants.FieldlessVariant()
```

fieldless 배리언트의 경우에도 싱글톤이라는 점을 기억해 주세요.

일반적으로는 유닛 배리언트를 사용하는 것이 권장되지만, 만약 fieldless 배리언트가 더 어울리는 경우가 있다면
사용해도 좋습니다.

### `unreachable`의 사용법

`unreachable`은 코드가 논리적으로 도달할 수 없지만 타입 체커를 위해서나 하위 호환성이 없는 미래의 변화 등에 제대로 된 오류를 내보내기 위한 목적으로 사용됩니다.

이 함수는 작성한 코드에 분명한 버그가 있을 때 나타나도록 디자인되어 있습니다.
사용자가 버그가 아닌 코드에서 `Unreachable` 오류를 만나는 일이 없도록 주의해 주세요.

다음의 경우를 확인해 봅시다.

```python
from fieldenum import Unit, Variant, fieldenum, unreachable

@fieldenum
class Option[T]:
    """실제 Option 구현의 단순화된 버전"""

    Nothing = Unit
    Some = Variant(T)

    def unwrap(self: Option[T]) -> T:
        match self:
            case Option.Nothing:
                raise ValueError("Unwrap failed!")

            case Option.Some(value):
                return value

            case other:
                unreachable(other)
```

이 코드에서는 `unreachable()`을 통해 코드를 방어합니다.

여기에는 세 가지 목적이 있습니다.

* 이는 타입 체커가 발생할 수 없는 결과를 가정하는 것을 방지합니다. `unreachable`이 없으면 타입 체커는 `unwrap` 함수가 매치되지 않고 통과할 가능성이 있다고 생각해 반환 타입을 `T | None`으로 잘못 인식합니다.
* 이는 `self`에 `Option` 이외의 타입이 왔을 때 생길 수 있는 오류를 방지합니다. 사용자가 `self`에 `Option` 외의 타입을 전달하면 조용히 `None`이 반환되는 것이 아니라 오류를 내보냅니다.
* 이는 미래의 하위 호환성 없는 변화가 일어났을 때 생길 수 있는 오류를 방지합니다.

이중 마지막 번째를 한번 더 살피겠습니다.
만약 `Nothing`으로는 부족해서 '뭔가 Nothing같지만 확실하지 않은' 값을 표현하기 위해 `Maybe` 배리언트를 추가한다면 어떻게 될까요?

```python
from fieldenum import Unit, Variant, fieldenum, unreachable

@fieldenum
class Option[T]:
    Nothing = Unit
    Some = Variant(T)
    Maybe = Unit

    def unwrap(self: Option[T]) -> T:
        match self:
            case Option.Nothing:
                raise ValueError("Unwrap failed!")

            case Option.Some(value):
                return value

            case other:
                unreachable(other)
```

이렇게 되면 기존의 코드들의 하위 호환성이 깨지게 되는데, 이때 `unreachable`을 사용한 `.unwrap()`의 구현은 오류를 통해 현재 상태가 잘못되어 보인다고 명확하게 알립니다.

이러한 `unreachable`의 사용은 없어도 99.9% 확률로 큰 문제가 없습니다(혹은 *없어야 합니다*). 따라서 빼먹더라도 재앙적인 일이 발생하지는 않으니 간단한 코드에서는 생략해도 됩니다.

하지만 여러 사람이 사용하는 라이브러리 등에서는 `unreachable`을 통해 잘못된 타입 추론을 막고 혹시 모를 미래에 생길 문제를 방지하는 것이 모두에게 좋습니다.

#### `unreachable`을 사용하면 안 되는 경우

앞서 설명한 경우가 `unreachable`이 유용한 거의 모든 경우입니다. 그 외의 경우에는 `unreachable`을 사용해서는 안 됩니다.

예를 들어 타입 힌트를 위반한 사용 정도는 `unreachable`이 사용되어서는 안 됩니다.

```python
def get_message(message: Option[str]):
    match message:
        case Some(value):
            print("Received:", value)

        case Option.Nothing:
            print("Nothing received.")

        case other:
            unreachable(other)  # XXX: 타입 체커를 어겨서 이곳에 도달할 수 있습니다.

get_message(123)  # will raise Unreachable (XXX)
```

그 대신 아래와 같이 짜야 합니다:

```python
def get_message(message: Option[str]):
    match message:
        case Some(value):
            print("Received:", value)

        case Option.Nothing:
            print("Nothing received.")

        case other:
            raise TypeError(f"Expect `Option` but received {other}.")  # GOOD

get_message(123)  # will raise TypeError (GOOD)
```

## Credits

이 프로젝트는 [러스트의 `Enum`](https://doc.rust-lang.org/reference/items/enumerations.html)에서 크게 영향을 받았으며, [rust_enum](https://github.com/girvel/rust_enum)에서 일부 디자인을 차용하였습니다.

또한 튜토리얼 중 일부는 [<러스트 프로그래밍 언어>의 '열거형 정의하기' 쳅터](https://doc.rust-kr.org/ch06-01-defining-an-enum.html)에서 발췌했습니다.

## Releases

* 0.1.0: 첫 릴리즈
