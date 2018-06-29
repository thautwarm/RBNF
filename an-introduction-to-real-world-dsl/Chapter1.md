领域特定语言
=======================

是什么
-------------------

- 针对特定领域，为了便利开发, 使用特定语法制造的语言。

你把Python看作是使用C开发的, 专用于各类脚本任务的DSL。

真的要讲什么是DSL, 当然是王垠讲得最好了: [DSL](http://www.yinwang.org/blog-cn/2017/05/25/dsl)。

(王垠先生如果看到，请发送支付宝账号到我邮箱，我当即转您30。等我有钱了，再给您100000软妹币

为什么
-----------------

减小维护和扩展成本，减少重复工作。

* SQL ORM的配置

    我懂，我懂。你们中搞后端的，数据库设计，维护，很累。我也做过一点，我也累。
    那么如果有一个DSL来搞定数据库的一切，不仅不会像王垠先生说的那样，
    
    > 带来严重的理解，交流和学习曲线问题，可能会严重的降低团队的工作效率。如果这个 DSL 是给用户使用，会严重影响用户体验，降低产品的可用性

    反而会让逻辑变得极其清晰, 可维护。
    下面是我实现的一个和Python的SQLAlchemy耦合的DSL([DBG-Lang](https://github.com/thautwarm/dbg-lang))，当然它很好移植到别的SQL框架。  

        ```
        User(id: int~)   # 定义表User, 主键 id, 使用 sequence
        {
            openid    : TextStr?                   # 可空
            account   : NameStr!                   # 唯一。
            # 后缀描述符可叠加 例如 account: NameStr?!
            password  : NameStr
            permission: Permission
            sex       : Sex         = Sex.unknown  # 默认值
            nickname  : NameStr?
            repr{
                id, nickname, permission  
                # 表示对象ToString包含如下信息，用于 logging
            }
        }
        User^ <-> Item{     # 建立一对一关系，^ 表示 User对Item具有所有权
            some: NameStr?  # extra data
        }
        User <<->> Course{  # 建立多对多关系
        }
        User <<-> Some{     # 建立多对一关系
        }
        ```  
    这不仅仅使得表设计和关系设计变得清晰可维护，而且，该语言的代码编译后还生成一些析构方法，例如删除`User`对象使用`delete_user`, 可以自动管理该`User`的关系。

    试想一下，假如来了新需求，要我们对数据库进行某些扩展，例如
    
    - 加一个表
    - 新增一些关系
    - 增加一些约束
    - 某个表加一个字段并且指定某种默认值
    - 添加索引

    有了这个DSL, 面对新需求只不过几或几十个的字符的变动。
    
    **你将永不需要`import sqlalchemy`或是写出一个新的`class`然后忘记添加关系或是修改表的关系配置**。

    这应该是一个值得深究的项目: 如何使用**最小精力**搞定数据库的各个方面。  
    谁要是因我受启发，开坑时请加我一个collaborator :)

* React JSX

    不是很懂，但是前端应该要找点例子。
    ```jsx
    function getGreeting(user) {
        if (user) {
            return <h1>Hello, {formatName(user)}!</h1>;
        }
        return <h1>Hello, Stranger.</h1>;
    }
    ```

    其实HTML及其相似物也是DSL。

* 数据提取

    在这里我假设有这样一个DSL从HTML中获取数据。

    ```

    <html>
        <head>
        <meta charset=@Charset> 
        </head> 
    <div>
        <div class=@ClassOfSecondLayout>
    </div>    

    </html>

    ```
    上面这个DSL将会提取两个数据`Charset, ClassOfSecondLayout`。  
    其中, `Charset`捕获了`html/head/meta`的`charset`取值，而`ClassOfSecondLayout`捕获了`html/div/div`中的`class`取值。
    
    这个DSL现在或许不是那么强力，语义也未足够明确，但他足够简单，好用。  
    **当老板要求你在别的网站提取相同的数据时，不需要项目源代码便可以满足新的需求**。  
    只需要进行再设计，很容易让他成为**极其便于维护和扩展**的数据提取工具。

    
    GraphQL是它的同类产品。


* 其他例子我还没想好。列举一些:
    
    ```
    SQL, 正则表达式, 
    ```


注意!!!!!
--------------------------------

DSL应当总是让事情变得简单，如果你发现你的DSL复杂到不能让人秒懂时，你应该思考这是不是太麻烦了。

一门语言如果进行正确的抽象，通常可以很好的解决大多数的问题。


怎么做
-----------------------------------

请看Chapter2



