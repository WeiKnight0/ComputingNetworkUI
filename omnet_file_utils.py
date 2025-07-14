import os

# 写入 network.ned 的具体内容（使用传入的文件对象）
def write_network_ned(f, typeNum=None, nodeList=None, channelList=None):
    # 示例：写一个简单的 OMNeT++ 网络模块结构
    write_dependent_source(f)
    f.write("\nnetwork TestNetwork \n{\n")

    f.write("\tparameters:\n\t\t@display(\"p=10,10;b=712,152;bgb=990,346\");\n")
    # f.write("\ttypes:\n\t\tchannel C extends ThruputMeteringChannel\n\t\t{\n")
    # f.write("\t\t\tdelay = 0.1us;\n\t\t\tdatarate = 100Mbps;\n\t\t\tthruputDisplayFormat = \"#N\";\n\t\t}\n")

    f.write("\tsubmodules:\n")
    write_submodules(f, typeNum)
    f.write("\tconnections allowunconnected:\n")
    write_connections(f, nodeList, channelList)
    f.write("}\n")

# 写入 omnetpp.ini 的具体内容
def write_omnetpp_ini(f, nodeList=None, channelList=None):
    '''f.write("[General]\n")
    f.write("network = TestNetwork\n")
    for i in range(3):  # 示例：设置每个节点的参数
        f.write(f"**.node{i}.numApps = 1\n")
        f.write(f"**.node{i}.app[0].typename = \"UdpBasicApp\"\n")'''
    f.write("test")

def write_dependent_source(f):
    f.write("package inet.examples.computing_power_network;\n\n")

    f.write("import inet.common.misc.ThruputMeteringChannel;\n")
    f.write("import inet.common.scenario.ScenarioManager;\n")
    f.write("import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;\n")
    f.write("import inet.computing_power_network.node.UserGateway.UserGateway;\n")
    f.write("import inet.node.ospfv2.OspfRouter;\n")
    f.write("import inet.node.inet.StandardHost;\n")
    f.write("import inet.applications.udpapp.UdpBasicApp;\n\n")

    f.write("import inet.computing_power_network.node.UserGateway;\n")
    f.write("import inet.computing_power_network.node.ComputingRouter;\n")
    f.write("import inet.computing_power_network.node.UserNode;\n")
    f.write("import inet.computing_power_network.node.ComputeNode;\n")
    f.write("import inet.computing_power_network.node.ComputeScheduleNode;\n\n")

def write_submodules(f, typeNum):
    for key, value in typeNum.items():
        if typeNum[key] != 0:
            f.write("\t\t%s[%d]: %s;\n"%(key, value, key))

def write_connections(f, nodeList, channelList):
    for channel in channelList:
        start_name = channel.start_item.nodetype + "[" + str(channel.start_item.index) + "]"
        end_name = channel.end_item.nodetype + "[" + str(channel.end_item.index) + "]"
        bandwidth = channel.bandwidth if channel.bandwidth != 0 else 100
        f.write("\t\t%s.ethg++ <--> ThruputMeteringChannel{bandwidth=%dMbps } <--> %s.ethg++;\n"
                %(start_name, bandwidth, end_name))
