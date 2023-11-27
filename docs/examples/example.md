
# Hello World

- ex01.stk
~~~ stacker
"Hello World" echo
~~~

~~~ bash
$ stacker hello_world.stk
Hello World
~~~

# FizzBuzz
- ex02.stk
~~~ stacker
1 100 seq {
    {"fizzbuzz" echo}
    {
        {"buzz" echo}
        {
            {"fizz" echo}
            {i str echo}
            i 3 % 0 ==
            ifelse
        }
        i 5 % 0 ==
        ifelse
    }
    i 3 % 0 == i 5 % 0 == and
    ifelse
} i for
~~~

~~~ bash
$ stacker fizzbuzz.stk
1
2
fizz
4
buzz
fizz
7
8
fizz
buzz
11
fizz
13
14
fizzbuzz
...
~~~
