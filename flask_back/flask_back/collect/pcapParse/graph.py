from py2neo import Graph,Node,Relationship


#数据库连接
graph1 = Graph(host='localhost',http_port=7978,user='neo4j',password='neo4j')
graph2 = Graph('http://localhost:7474/browser/',user='neo4j',password='neo4j')
graph3 = Graph('https://localhost:7473/browser/', user='neo4j', password='neo4j')
graph4 = Graph(password='neo4j')

# 添加节点
node = Node('label',name='label_name')  # label为节点标签，name为节点名称，需要注意不要用label='label'否则label会成为节点的的属性
node['property'] = 'property_info'    # 向node添加属性'property'
node.setdefault('age',18)    # 通过setdefault()方法赋值默认属性
graph.merge(node)    # 将节点加入图数据库与create不同之处在于若节点存在则不创建
graph.commit()    # 提交图数据库的变更

# 创建关系
a=Node("People",name='a')
b=Node("People",name='b')
relationship = Relationship(a,'Realize',b)    # 创建a与b之间的Realize关系
relationship['date']='20181101'    # 在关系上添加data属性
graph.merge(a) 
graph.merge(b)
graph.merge(relationship)    # 将关系加入图数据库
graph.commit()

graph = Graph("http://localhost:7474",auth=("neo4j","password"))
a = Node("Person", name="Alice")
b = Node("Person", name="Bob")
ab = Relationship(a, "KNOWS", b)
graph.create(ab)
#创建Relationship
Relationship(*start_node*, *type*, *end_node*, ***properties*)
#返回Relationship的property
Relationship[key]
#删除某个property
del Relationship[key]
#将relationship的所有property以dictionary的形式返回
dict(relationship)

graph.nodes.match(self, *labels, **properties)# 找到所有的nodes，

graph = Graph()
matcher = NodeMatcher(graph)
matcher.match("Person", name="Keanu Reeves").first()
#结果 (_224:Person {born:1964,name:"Keanu Reeves"})

# where里面使用_指向当前node
list(matcher.match("Person").where("_.name =~ 'K.*'"))

graph.match(nodes=None, r_type=None, limit=None) #找到所有的relationships

from py2neo import Graph, NodeMatcher, Subgraph

tx = graph.begin()
# 找到你要找的Nodes
matcher = NodeMatcher(graph)
nodes = matcher.match("User")
# 将返回的“Match”类转成list
new_nodes = list(nodes)
## 添加你要修改的东西
for node in new_nodes:
    node['tag'] = node['tag'].split(',')
# 里面是Node的list可以作为Subgraph的参数
sub = Subgraph(nodes=new_nodes)
# 调用push更新
tx.push(sub)
tx.commit()

tx = graph.begin()
nodes=[]
for line in lineLists:
    oneNode = Node()
    ........
    #这里的循环，一般是把文件的数据存入node中
    nodes.append(oneNode)
nodes=neo.Subgraph(nodes)
tx.create(nodes)
tx.commit()

graph.run("MATCH (p:Post),(u:User) \
                WHERE p.OwnerUserId = u.Id \
                CREATE (u)-[:Own]->(p)")