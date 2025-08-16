from PySide6.QtWidgets import (QGraphicsItemGroup, QGraphicsRectItem, QGraphicsSimpleTextItem)
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainterPath

class EventTraceItem:
    """表示单个调度事件的类"""
    def __init__(self, sim_time, packet_type, packet_id, 
                 source_node_type, source_node_id, dest_node_type, dest_node_id):
        self.sim_time = sim_time
        self.packet_type = packet_type  # 消息类型
        self.packet_id = packet_id      # 消息ID
        self.source_node_type = source_node_type  # 统一使用下划线命名
        self.source_node_id = source_node_id
        self.dest_node_type = dest_node_type
        self.dest_node_id = dest_node_id
        
    def __str__(self) -> str:
        return (f"Time: {self.sim_time}, Type: {self.packet_type}, ID: {self.packet_id}, "
                f"Src: ({self.source_node_type},{self.source_node_id}), Dst: ({self.dest_node_type},{self.dest_node_id})")

class EventFlowAnimation:
    """数据包流动动画类，带实心线拖尾效果和渐隐消失"""
    # 消息类型中文名称映射
    MESSAGE_TYPE_NAMES = {
        1: "任务上报",
        2: "算力节点状态采集",
        3: "网络状态采集",
        4: "算力节点状态更新",
        5: "网络状态上报",
        6: "任务决策",
        7: "任务传输",
        8: "任务结果",
        9: "任务评估"
    }
    
    def __init__(self, source_node, dest_node, packet_type, packet_id, scene, sim_time, source_node_id):
        self.source_node = source_node
        self.dest_node = dest_node
        self.packet_type = packet_type
        self.packet_id = packet_id
        self.scene = scene
        self.progress = 0.0  # 动画进度 (0.0-1.0)
        self.fade_progress = 0.0  # 渐隐进度 (0.0-1.0)
        self.is_complete = False
        self.source_node_id = source_node_id  # 保存源节点完整ID（如"用户节点3"）

        # 消息类型对应的颜色
        self.type_colors = {
            1: QColor(255, 0, 0),    # 任务上报消息
            2: QColor(255, 127, 0),  # 算力节点状态采集消息
            3: QColor(255, 255, 0),  # 网络状态采集消息
            4: QColor(0, 255, 0),    # 算力节点状态更新消息
            5: QColor(0, 0, 255),    # 网络状态上报消息
            6: QColor(148, 0, 211),  # 决策消息
            7: QColor(255, 0, 255),  # 任务传输消息
            8: QColor(0, 255, 255),  # 结果消息
            9: QColor(128, 128, 128) # 评估消息
        }
        
        # 拖尾效果配置
        self.trail_path = QPainterPath()  # 完整拖尾路径
        self.current_trail_path = QPainterPath()  # 当前显示的拖尾路径
        self.trail_item = None            # 拖尾图形项
        self.trail_width = 3              # 拖尾线宽
        self.total_flow_time = 1.0   # 传输所需时间，用于渐隐持续时间
        self.start_time = None            # 动画开始时间
        
        # 创建名称标签
        self.create_name_label()

        # 创建动画元素
        self.create_animation_items()

        
    def create_animation_items(self):
        """创建动画元素"""
        print("创建动画元素中",end=' ')
        # 创建移动的点，表示数据包
        self.dot_item = self.scene.addEllipse(0, 0, 6, 6, 
                                       QPen(Qt.NoPen), 
                                       QBrush(self.type_colors.get(self.packet_type, QColor(0,0,0))))
        self.dot_item.setZValue(3)  # 确保点在最上方
        
        # 初始化拖尾路径
        start_point = self.get_node_center(self.source_node)
        self.trail_path.moveTo(start_point)
        self.current_trail_path.moveTo(start_point)
        
        # 创建拖尾图形项
        self.trail_item = self.scene.addPath(
            self.current_trail_path, 
            QPen(self.type_colors.get(self.packet_type, QColor(0,0,0)), self.trail_width)
        )
        self.trail_item.setZValue(2)  # 拖尾在数据包下方
        
        # 设置初始位置
        self.update_position()
        print("创建成功！",end='\n')
        
    def get_node_center(self, node):
        """获取节点中心位置"""
        return node.scenePos() + QPointF(node.boundingRect().width()/2, node.boundingRect().height()/2)
        
    def update(self, current_time):
        """更新动画状态，使用绝对时间而非进度值"""
        if self.start_time is None:
            self.start_time = current_time
            
        elapsed_time = current_time - self.start_time
        
        # 计算进度（0.0-1.0）
        if elapsed_time < self.total_flow_time:
            self.progress = elapsed_time / self.total_flow_time
            self.update_position()
            return False  # 动画未完成
        elif self.fade_progress < 1.0:
            # 动画完成，但渐隐过程未完成
            if not self.is_complete:
                self.is_complete = True
                
                # 移除数据包点
                if self.dot_item and self.dot_item.scene():
                    self.scene.removeItem(self.dot_item)
                self.dot_item = None
                
            # 增加渐隐进度，使用与流动相同的时间基准
            elapsed_fade_time = elapsed_time - self.total_flow_time
            self.fade_progress = min(1.0, elapsed_fade_time / self.total_flow_time)
            
            # 更新渐隐中的拖尾
            self.update_fade()
            
            return False  # 渐隐过程未完成
        else:
            # 彻底清理拖尾和名称标签
            if self.trail_item and self.trail_item.scene():
                self.scene.removeItem(self.trail_item)
            self.trail_item = None
            self.trail_path = None
            self.current_trail_path = None
            
            # 移除名称标签
            if self.name_item and self.name_item.scene():
                self.scene.removeItem(self.name_item)
            self.name_item = None
            
            return True  # 动画和渐隐都完成    
    
    def update_position(self):
        """更新点的位置，添加拖尾效果"""
        if self.dot_item and self.trail_item:
            # 沿直线计算当前位置
            start_point = self.get_node_center(self.source_node)
            end_point = self.get_node_center(self.dest_node)
            
            # 当前位置
            current_x = start_point.x() + (end_point.x() - start_point.x()) * self.progress
            current_y = start_point.y() + (end_point.y() - start_point.y()) * self.progress
            
            # 更新完整拖尾路径
            self.trail_path.lineTo(current_x, current_y)
            
            # 如果动画还在进行中，更新当前拖尾路径
            if not self.is_complete:
                self.current_trail_path = QPainterPath(self.trail_path)
                self.trail_item.setPath(self.current_trail_path)
            
            # 设置数据包位置
            self.dot_item.setPos(current_x - 3, current_y - 3)

            # 更新名称位置
            self.update_name_position()

    def create_name_label(self):
        """创建数据包名称标签，格式为 消息名称(发出消息的用户ID-第几个消息)"""
        # 从源节点ID中提取用户ID数字部分（如从"用户节点3"提取"3"）
        user_id = ''.join(filter(str.isdigit, str(self.source_node_id)))
        
        # 获取消息类型名称
        message_name = self.MESSAGE_TYPE_NAMES.get(self.packet_type, f"未知消息({self.packet_type})")
        
        # 生成新格式的名称：消息名称(用户ID-第几个消息)
        name = f"{message_name}({user_id}-{self.packet_id})"
        
        # 创建文本项
        self.name_item = self.scene.addText(name)
        self.name_item.setDefaultTextColor(self.type_colors.get(self.packet_type, QColor(0,0,0)))
        self.name_item.setZValue(4)  # 确保文本在最上方
        
        # 设置字体和大小，确保显示清晰
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.name_item.setFont(font)
        
    def update_name_position(self):
        """更新名称标签位置，跟随数据包移动"""
        if self.name_item and self.dot_item:
            # 获取数据包位置
            packet_pos = self.dot_item.pos()
            
            # 计算文本位置（在数据包上方居中）
            text_width = self.name_item.boundingRect().width()
            text_height = self.name_item.boundingRect().height()
            
            # 设置文本位置
            self.name_item.setPos(
                packet_pos.x() + 3 - text_width / 2,  # 水平居中
                packet_pos.y() - text_height - 5     # 垂直上方
            )
    
    def update_fade(self):
        """更新渐隐过程中的拖尾显示，从起始节点开始消失"""
        if self.trail_item and self.trail_path:
            # 创建新的路径，只包含需要保留的部分
            new_path = QPainterPath()
            
            # 获取完整路径长度
            path_length = self.trail_path.length()
            
            # 计算应该移除的路径长度（从起点开始移除）
            remove_length = path_length * self.fade_progress
            
            # 如果还有要保留的部分
            if remove_length < path_length:
                # 计算保留部分的起点百分比
                start_percent = remove_length / path_length
                
                # 从保留部分的起点开始
                new_path.moveTo(self.trail_path.pointAtPercent(start_percent))
                
                # 分段添加路径，确保平滑
                segments = 20  # 分段数
                for i in range(1, segments + 1):
                    t = start_percent + (1.0 - start_percent) * (i / segments)
                    if t <= 1.0:
                        new_path.lineTo(self.trail_path.pointAtPercent(t))
                
                # 更新拖尾显示
                self.current_trail_path = new_path
                self.trail_item.setPath(self.current_trail_path)
            else:
                # 如果没有要保留的部分，清空路径
                self.current_trail_path = QPainterPath()
                self.trail_item.setPath(self.current_trail_path)    
    
    def is_finished(self):
        """检查动画是否完成"""
        return self.fade_progress >= 1.0

    def remove_animation(self):
        """安全地从场景中移除动画的所有元素"""
        # 移除数据包点
        if hasattr(self, 'dot_item') and self.dot_item and self.dot_item.scene():
            self.scene.removeItem(self.dot_item)
            self.dot_item = None

        # 移除拖尾路径
        if hasattr(self, 'trail_item') and self.trail_item and self.trail_item.scene():
            self.scene.removeItem(self.trail_item)
            self.trail_item = None

        # 移除名称标签
        if hasattr(self, 'name_item') and self.name_item and self.name_item.scene():
            self.scene.removeItem(self.name_item)
            self.name_item = None

        # 重置所有路径引用
        self.trail_path = None
        self.current_trail_path = None

        # 标记为已完成
        self.is_complete = True
        self.fade_progress = 1.0
 
class Event:
    """事件类，用于表示数据包传输事件"""
    def __init__(self, event_id, source_node_type, source_node_id, dest_node_type, dest_node_id, packet_type, sim_time):
        self.event_id = event_id
        self.source_node_type = source_node_type
        self.source_node_id = source_node_id
        self.dest_node_type = dest_node_type
        self.dest_node_id = dest_node_id
        self.packet_type = packet_type
        self.sim_time = sim_time
