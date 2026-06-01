import genesis as gs
import numpy as np
import tempfile
import os

gs.init(
    seed = None,
    debug = True,
    backend = gs.gpu,
    logger_verbose_time = False
)

# 创建场景
scene = gs.Scene(
    sim_options = gs.options.SimOptions(
        dt = 0.01,                # 仿真步长 0.01秒
        gravity = (0, 0, -10.0),  # 重力加速度
    ),
    show_viewer = True,           # 显示可视化窗口
    viewer_options = gs.options.ViewerOptions(
        camera_pos = (1.0, -2.0, 1.5),
        camera_lookat = (1.0, 0, 1.0),
        camera_fov = 60,
    ),
)

# 地面
plane = scene.add_entity(
    morph = gs.morphs.Plane(),
)

# 添加刚体小球
ball = scene.add_entity(
    material = gs.materials.Rigid(),          # 刚体材质（不受形变）
    morph = gs.morphs.Sphere(
        radius = 0.05,                        # 半径 0.05 米
    ),
    surface = gs.surfaces.Default(
        color = (1.0, 0.2, 0.2),             # 红色
        vis_mode = 'visual',                 # 渲染为光滑网格（默认）
    ),
)

# ========== 2. 桌子（尺寸：长1.0, 宽0.5, 高0.8）==========
table = scene.add_entity(
    gs.morphs.Box(size=(1.0, 0.5, 0.8), fixed=True),  # 固定不动
)

# ========== 斜面+水平面 ==========
width_y = 0.2           # Y轴方向宽度（轨道宽度）
L_slope = 0.6           # 斜面水平投影长度
L_flat = 0.5           # 水平面长度
H_slope = 1.47           # 斜面起点高度
thick_y_flat = 0.05        # 底板厚度（视觉与碰撞）
thick_y_slope = 0.07      # 斜面y轴方向厚度
H_flat = 0.85            # 水平面高度
verts = np.array([
    # 斜面部分
    [0, 0, H_slope],        # 0 前顶
    [L_slope, 0, H_flat],        # 1 前底
    [0, width_y, H_slope],  # 2 后顶
    [L_slope, width_y, H_flat],  # 3 后底
    # 水平面部分
    [L_slope, 0, H_flat],        # 4 前起点（与1相同）
    [L_slope+L_flat, 0, H_flat], # 5 前终点
    [L_slope, width_y, H_flat],  # 6 后起点（与3相同）
    [L_slope+L_flat, width_y, H_flat], # 7 后终点
    #底板部分
    #斜面
    [0, 0, H_slope - thick_y_slope], # 8 底前顶
    [L_slope, 0, H_flat - thick_y_slope],        # 9 底前底
    [0, width_y, H_slope - thick_y_slope],  # 10 底后顶
    [L_slope, width_y, H_flat - thick_y_slope],  # 11 底后底
    #水平面
    [L_slope, 0, H_flat - thick_y_flat],        # 12 底前起点（与9相同）
    [L_slope+L_flat, 0, H_flat - thick_y_flat], # 13 底前终点
    [L_slope, width_y, H_flat - thick_y_flat],  # 14 底后起点（与11相同）
    [L_slope+L_flat, width_y, H_flat - thick_y_flat] # 15 底后终点
], dtype=np.float32)

'''
# 定义三角形面（每个矩形面由两个三角形拼成）
faces = np.array([
    # 斜面顶面（两个三角形）
    [0,1,2], [1,3,2],
    # 水平面顶面
    [4,6,5], [5,7,6],
    # 斜面侧面
    [8,0,9], [9,0,1],
    [2,10,3], [3,10,11],
    # 斜面底面
    [10,8,11], [11,8,9],
    # 水平面侧面
    [12,4,13], [13,4,5],
    [6,14,7], [7,14,15],
    # 水平面底面
    [14,12,15],[15,12,13]
], dtype=np.uint32)
'''
faces = np.array([
    # 斜面顶面
    [0,2,3,1],
    # 水平面顶面
    [4,5,7,6],
    # 斜面侧面
    [8,9,1,0],
    [2,3,11,10],
    [2,10,8,0],
    # 斜面底面
    [10,11,9,8],
    # 水平面侧面
    [12,13,5,4],
    [6,7,15,14],
    [5,13,15,7],
    # 水平面底面
    [14,15,13,12]
], dtype=np.uint32)

# ========== 写入临时 OBJ 文件 ==========
with tempfile.NamedTemporaryFile(mode='w', suffix='.obj', delete=False) as tmp:
    for v in verts:
        tmp.write(f"v {v[0]} {v[1]} {v[2]}\n")
    for face in faces:
        '''
        # OBJ 索引从 1 开始，且需确保每个面是三角形（三个顶点）
        i1, i2, i3 = face + 1
        tmp.write(f"f {i1} {i2} {i3}\n")
        '''
        i1, i2, i3, i4 = face + 1
        tmp.write(f"f {i1} {i2} {i3} {i4}\n")
    obj_path = tmp.name

# ========== 添加斜坡实体（固定） ==========
ramp = scene.add_entity(
    morph=gs.morphs.Mesh(file=obj_path, fixed=True),   # 从文件加载网格
    material=gs.materials.Rigid(),                     # 刚体材质
    surface=gs.surfaces.Default(
        color=(0.7, 0.7, 0.7),
        vis_mode='visual'
    ),
)

# ========== 4. 构建场景并设置位置 ==========
scene.build()

# 设置桌子的位置
table.set_pos(np.array([0.5, 0.25, 0.4]))

# 球体的初始位置
ball.set_pos(np.array([0.0, 0.25, 1.42]))  # 完全贴合斜坡

# 斜坡的初始位置（将斜坡最高处最前点左移0.1，后移0.15）
ramp.set_pos(np.array([-0.1, 0.15, 0.0]))

print("场景已创建完成：无弹性球体、桌子、斜坡实体已添加并定位。")

# 运行仿真
for _ in range(100000000):
    scene.step()
