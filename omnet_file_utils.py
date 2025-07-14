import os
from allTypeItem import *

# 写入 network.ned 的具体内容（使用传入的文件对象）
def write_network_ned(f, typeNum=None, nodeList=None, channelList=None):
    # 示例：写一个简单的 OMNeT++ 网络模块结构
    write_dependent_source(f)
    f.write("\nnetwork TestNetwork \n{\n")

    f.write("\tparameters:\n\t\t@display(\"p=10,10;b=712,152;bgb=990,346\");\n")
    f.write("\ttypes:\n\t\tchannel C extends ThruputMeteringChannel\n\t\t{\n")
    f.write("\t\t\tdelay = 0.1us;\n\t\t\tdatarate = 100Mbps;\n\t\t\tthruputDisplayFormat = \"#N\";\n\t\t}\n")

    f.write("\tsubmodules:\n")
    write_submodules(f, nodeList)
    f.write("\tconnections:\n")
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
    f.write("import inet.node.ospfv2.OspfRouter;\n")
    f.write("import inet.node.inet.StandardHost;\n")
    f.write("import inet.applications.udpapp.UdpBasicApp;\n\n")

    f.write("import inet.computing_power_network.node.UserGateway;\n")
    f.write("import inet.computing_power_network.node.ComputingGateway;\n")
    f.write("import inet.computing_power_network.node.UserNode;\n")
    f.write("import inet.computing_power_network.node.ComputeNode;\n")
    f.write("import inet.computing_power_network.node.ComputeScheduleNode;\n\n")

def write_submodules(f, nodeList):
    def getNodeName(original_name):
        """
        将中文节点名称转换为英文格式（序号=1时去除1，序号>1时保留数字）
        示例：
            "用户节点1" -> "UserNode"
            "算力节点2" -> "ComputingNode2"
            "调度决策网关" -> "DecisionRouter"
        """
        # 中文类型到英文类型的映射
        type_dict = {
            "用户节点": "UserNode",
            "算力节点": "ComputingNode",
            "用户网关": "UserGateway",
            "算力网关": "ComputingGateway",
            "调度决策网关": "DecisionRouter",
            "路由器": "Router"
        }
        # 分离中文类型和数字后缀
        for cn_name, en_name in type_dict.items():
            if original_name.startswith(cn_name):
                suffix = original_name[len(cn_name):]
                # 处理数字后缀
                if suffix.isdigit(): # 序号>1时保留
                    return f"{en_name}{suffix}"
                else:  # 无数字后缀或非数字字符
                    break
        # 未匹配到已知类型时返回None
        raise TypeError('错误的节点名称')

    for node in nodeList:
        # name = node.name
        f.write('\t\t' + getNodeName(node.name)+':'+ ('OspfRouter' if node.nodetype == 'Router' else node.nodetype) +'{\n')
        if node.nodetype == 'Router' or node.nodetype == 'ComputeGateway':
            f.write('\t\t\tparameters:\n\t\t\t\thasStatus=true;\n')
        f.write('\t\t\tgates:\n')
        f.write(f'\t\t\t\tethg[{len(node.channelList)}];\n')
        f.write('\t\t}\n')
        pass

def write_connections(f, nodeList, channelList):
    for channel in channelList:
        start_name = channel.start_item.nodetype # + "[" + str(channel.start_item.index) + "]"
        start_index = channel.start_item.index
        end_name = channel.end_item.nodetype # + "[" + str(channel.end_item.index) + "]"
        end_index = channel.end_item.index
        # bandwidth = channel.bandwidth if channel.bandwidth != 0 else 100
        f.write("\t\t%s.ethg[%d] <--> C <--> %s.ethg[%d];\n"
                %(start_name, start_index, end_name,end_index))


def write_xml(file, nodeList, channelList):
    # 写入 XML 头部
    file.write('<?xml version="1.0"?>\n')
    file.write('<OSPFASConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="OSPF.xsd">\n\n')

    # 写入主干区域（Area 0.0.0.0）
    file.write('  <!-- Area 0.0.0.0: 主干区域，包含所有节点和连接的网段 -->\n')
    file.write('  <Area id="0.0.0.0">\n')

    # 写入连接的地址范围
    for channel in channelList:
        start_name = channel.start_item.name
        end_name = channel.end_item.name
        file.write(f'    <AddressRange address="{start_name}>{end_name}" mask="255.255.255.0" />\n')
        file.write(f'    <AddressRange address="{end_name}>{start_name}" mask="255.255.255.0" />\n')

    # 写入节点的地址范围
    for node in nodeList:
        if node.nodetype in ["UserNode", "ComputingNode", "DecisionRouter"]:
            file.write(f'    <AddressRange address="{node.name}" mask="255.255.255.0" />\n')

    file.write('  </Area>\n\n')

    # 写入路由器配置
    for node in nodeList:
        if node.nodetype in ["Router", "UserGateway", "ComputingGateway"]:
            file.write(f'  <Router name="{node.name}" RFC1583Compatible="true">\n')

            # 为每个接口生成配置
            for i, channel in enumerate(node.channelList):
                interface_type = "PointToPointInterface"  # 默认点对点接口
                # 如果是连接用户或计算节点的接口，可能是广播接口
                if channel.another_point_of_channel(node).nodetype in ["UserNode", "ComputingNode"]:
                    interface_type = "BroadcastInterface"

                file.write(f'    <{interface_type} ifName="eth{i}" area="0.0.0.0" interfaceOutputCost="1" />\n')

            file.write('  </Router>\n\n')

    # 关闭根元素
    file.write('</OSPFASConfig>\n')