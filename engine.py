# -*- coding: utf-8 -*-

import uiautomator2 as u2
import json
import time
import random
import xml.etree.ElementTree as ET
from lxml import etree
import re
import os
import sys
import string
import logging
from util import save_image, remove_unicode, bezier_curve
from enums import Direction, Action, SelectorType
from collections.abc import Iterable

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_content(device, selectors, output_file="output.json"):
    """提取页面元素内容并保存到文件，支持多个选择器"""
    extracted_data = {}
    for alias, selector in selectors.items():
        try:    
            element = get_element(device, selector)
            if element:
                content = element.info
                extracted_data[alias] = content.get('text')
                logging.info(f"提取到元素 '{alias}' 的内容并保存: {content}")
            else:
                logging.error(f"未找到元素: {selector} (别名: {alias})")
        except Exception as e:
            logging.error(f"保存文件失败: {alias} : {selector}")
        # 将提取的数据保存到文件
    with open(output_file, 'a',encoding='utf-8') as f:
        f.write(json.dumps(extracted_data, ensure_ascii=False) + '\n')
    logging.info(f"所有内容已保存到文件: {output_file}")
          


def repeat_times(event, device):
    """按指定的次数重复执行事件"""
    times = event.get('times', 1)
    for i in range(times):
        for action_event in event.get('actions', [event]):
            executed = handle_event(action_event, device, i)
            if executed in ['continue', 'break', 'exit']:
                break
        if executed in ['continue', 'break', 'exit', True]:
            break

def extract_nodes(node, attribute_name):
    """递归函数用于提取带有指定属性的节点"""
    result = []
    if attribute_name in node.attrib:
        result.append(node.attrib[attribute_name])
    for child in node:
        result.extend(extract_nodes(child, attribute_name))
    return result

def perform_swipe_pagination(device, direction, pages=1, duration=0.5):
    """执行滑动翻页操作"""
    width, height = device.window_size()
    logging.info(f"设备屏幕大小: {width}x{height}")
    offset_x = width * 0.05
    offset_y = height * 0.05

    for _ in range(pages):
        start_x, start_y, end_x, end_y = calculate_swipe_coordinates(direction, width, height, offset_x, offset_y)
        logging.info(f"从 ({start_x}, {start_y}) 滑动到 ({end_x}, {end_y})")
        device.swipe(start_x, start_y, end_x, end_y, duration)
        time.sleep(1)  # 滑动之间的延迟模拟人类行为

def calculate_swipe_coordinates(direction, width, height, offset_x, offset_y):
    """计算滑动的起点和终点坐标"""
    if direction == Direction.UP:
        start_x = width / 2 + random.uniform(-offset_x, offset_x)
        start_y = height * 0.8 + random.uniform(-offset_y, offset_y)
        end_x = start_x
        end_y = height * 0.2 + random.uniform(-offset_y, offset_y)
    elif direction == Direction.DOWN:
        start_x = width / 2 + random.uniform(-offset_x, offset_x)
        start_y = height * 0.2 + random.uniform(-offset_y, offset_y)
        end_x = start_x
        end_y = height * 0.8 + random.uniform(-offset_y, offset_y)
    elif direction == Direction.LEFT:
        start_x = width * 0.8 + random.uniform(-offset_x, offset_x)
        start_y = height / 2 + random.uniform(-offset_y, offset_y)
        end_x = width * 0.2 + random.uniform(-offset_x, offset_x)
        end_y = start_y
    elif direction == Direction.RIGHT:
        start_x = width * 0.2 + random.uniform(-offset_x, offset_x)
        start_y = height / 2 + random.uniform(-offset_y, offset_y)
        end_x = width * 0.8 + random.uniform(-offset_x, offset_x)
        end_y = start_y
    else:
        logging.warning(f"未知的方向: {direction}")
        return 0, 0, 0, 0
    return start_x, start_y, end_x, end_y

def execute_workflow(workflow, device):
    """执行指定的工作流"""
    for event in workflow['events']:
        repeat_times(event, device)
    logging.info(f"工作流执行成功")

def handle_event(event, device, iteration):
    """处理单个事件"""
    if "actions" in event:
        # 递归处理嵌套的actions
        repeat_times(event, device)
        return

    if "selector" in event:
        index = event['selector']['value']
        if '{{index}}' in index:
            start = event['selector'].get('start', 0)
            event['selector']['value'] = index.replace('{{index}}', str(start + iteration + 1))
        executed = execute_event(event, device)
        event['selector']['value'] = index
        return executed
    return execute_event(event, device)


def execute_event(event, device):
    """执行单个事件"""
    action = Action[event['action'].upper()]
    if action == Action.LAUNCH_APP:
        perform_launch_app(device, event['package_name'], event.get('use_monkey', False))
    elif action == Action.STOP_APP:
        perform_stop_app(device, event['package_name'])
    elif action == Action.CLICK:
        perform_click(device, event['selector'], click_type=event.get('action_type'))
    elif action == Action.INPUT:
        perform_input(device, event['selector'], event['text'])
    elif action == Action.SWIPE:
        perform_swipe(device, Direction[event['direction'].upper()], event['duration'])
    elif action == Action.PULL_TO_REFRESH:
        perform_pull_to_refresh(device, event['duration'])
    elif action == Action.SWIPE_PAGINATION:
        perform_swipe_pagination(device, Direction[event['direction'].upper()], event.get('pages', 1), event.get('duration', 1))
    elif action == Action.WAIT_FOR_ELEMENT:
        return handle_wait_for_element(device, event)
    elif action == Action.EXTRACT_CONTENT:
        selectors = event['selectors']
        output_file = event.get('output_file', 'output.json')
        extract_content(device, selectors, output_file)
    elif action == Action.BACK:
        device.press("back")
    else:
        logging.warning(f"未知的动作: {action}")

def handle_wait_for_element(device, event):
    """处理等待元素的事件"""
    timeout = event.get('timeout', 10)
    if wait_for_element(device, event['selector'], timeout):
        return True
    return event["on_timeout"]["action"]

def perform_pull_to_refresh(device, duration=0.5):
    """执行下拉刷新操作"""
    width, height = device.window_size()
    logging.info(f"设备屏幕大小: {width}x{height}")
    start_x = width / 2 + random.uniform(-width * 0.05, width * 0.05)
    start_y = height * 0.2 + random.uniform(-height * 0.05, height * 0.05)
    end_x = start_x
    end_y = height * 0.8 + random.uniform(-height * 0.05, height * 0.05)
    
    logging.info(f"从 ({start_x}, {start_y}) 滑动到 ({end_x}, {end_y})")
    device.swipe(start_x, start_y, end_x, end_y, duration)

def perform_launch_app(device, package_name, use_monkey=False):
    """启动指定的应用程序"""
    logging.info(f"启动应用: {package_name}")
    device.app_start(package_name, use_monkey=use_monkey)
    time.sleep(2)  # 等待应用启动

def perform_stop_app(device, package_name):
    """停止指定的应用程序"""
    logging.info(f"停止应用: {package_name}")
    device.app_stop(package_name)
    time.sleep(2)  # 等待应用停止

def perform_click(device, selector, timeout=10, click_type=""):
    """执行点击操作"""
    xpath_type = selector.get("type")
    if xpath_type =="position":
        x= selector.get("value").get("x")
        y= selector.get("value").get("y")
        screen_width, screen_height = device.window_size()
        device.click(int(screen_width*x),int(screen_height*y))

    elif wait_for_element(device, selector, timeout):
        is_all = click_type == 'all'
        elements = get_element(device, selector, is_all=is_all)
        if isinstance(elements, Iterable):
            logging.info(f"点击元素: {selector}")
            for el in elements:
                el.click()
        elif elements:
            elements.click()
        else:
            logging.error(f"未找到元素: {selector}")
    else:
        logging.error(f"未在 {timeout} 秒内找到元素: {selector}")

def perform_input(device, selector, text, timeout=10):
    """执行输入操作"""
    if wait_for_element(device, selector, timeout):
        element = get_element(device, selector)
        if element:
            logging.info(f"输入文本 '{text}' 到元素: {selector}")
            element.click()
            device.send_keys(text, clear=True)
            device.press('enter')
        else:
            logging.error(f"未找到元素: {selector}")
    else:
        logging.error(f"未在 {timeout} 秒内找到元素: {selector}")

def perform_swipe(device, direction, duration=0.5):
    """执行滑动操作"""
    width, height = device.window_size()
    logging.info(f"设备屏幕大小: {width}x{height}")
    
    offset_x = width * 0.05
    offset_y = height * 0.05
    
    p0, p1, p2 = calculate_bezier_points(direction, width, height, offset_x, offset_y)
    steps = 50  # 生成沿曲线的点数
    points = [bezier_curve(p0, p1, p2, t / steps) for t in range(steps + 1)]
    for i in range(len(points) - 1):
        start_x, start_y = points[i]
        end_x, end_y = points[i + 1]
        device.swipe(start_x, start_y, end_x, end_y, duration / steps)
        time.sleep(duration / steps / 2)  # 滑动之间的小延迟

def calculate_bezier_points(direction, width, height, offset_x, offset_y):
    """计算贝塞尔曲线的控制点"""
    if direction == Direction.UP:
        p0 = (width / 2 + random.uniform(-offset_x, offset_x), height * 0.8 + random.uniform(-offset_y, offset_y))
        p2 = (p0[0], height * 0.2 + random.uniform(-offset_y, offset_y))
        p1 = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2 - height * 0.2)
    elif direction == Direction.DOWN:
        p0 = (width / 2 + random.uniform(-offset_x, offset_x), height * 0.2 + random.uniform(-offset_y, offset_y))
        p2 = (p0[0], height * 0.8 + random.uniform(-offset_y, offset_y))
        p1 = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2 + height * 0.2)
    elif direction == Direction.LEFT:
        p0 = (width * 0.8 + random.uniform(-offset_x, offset_x), height / 2 + random.uniform(-offset_y, offset_y))
        p2 = (width * 0.2 + random.uniform(-offset_x, offset_x), p0[1])
        p1 = ((p0[0] + p2[0]) / 2 - width * 0.2, (p0[1] + p2[1]) / 2)
    elif direction == Direction.RIGHT:
        p0 = (width * 0.2 + random.uniform(-offset_x, offset_x), height / 2 + random.uniform(-offset_y, offset_y))
        p2 = (width * 0.8 + random.uniform(-offset_x, offset_x), p0[1])
        p1 = ((p0[0] + p2[0]) / 2 + width * 0.2, (p0[1] + p2[1]) / 2)
    else:
        logging.warning(f"未知的方向: {direction}")
        return 0, 0, 0
    return p0, p1, p2

def get_element(device, selector, is_all=False):
    """根据选择器获取元素"""
    selector_type = SelectorType[selector['type'].upper()]
    value = selector['value']
    if selector_type == SelectorType.TEXT:
        return device(text=value)
    elif selector_type == SelectorType.RESOURCE_ID:
        return device(resourceId=value)
    elif selector_type == SelectorType.DESCRIPTION:
        return device(description=value)
    elif selector_type == SelectorType.XPATH:
        return device.xpath(value).all() if is_all else device.xpath(value)
    else:
        logging.error(f"未知的选择器类型: {selector_type}")
        return None

def safe_exit():
    """实现安全退出的操作，比如记录日志、释放资源等"""
    logging.info("执行安全退出操作")
    # 此处添加实际的安全退出逻辑

def wait_for_element(device, selector, timeout=10, auto_safe_exit=False):
    """等待元素出现"""
    selector_type = SelectorType[selector['type'].upper()]
    value = selector['value']
    logging.info(f"等待元素: {value}")

    try:
        element_found = check_element_presence(device, selector_type, value, timeout)
        if not element_found and auto_safe_exit:
            logging.warning(f"元素未在 {timeout} 秒内找到: {value}")
            safe_exit()
        return element_found
    except Exception as e:
        logging.error(f"等待元素时发生错误: {e}")
        if auto_safe_exit:
            safe_exit()
        return False

def check_element_presence(device, selector_type, value, timeout):
    """检查元素是否存在"""
    if selector_type == SelectorType.TEXT:
        return device(text=value).wait(timeout=timeout)
    elif selector_type == SelectorType.RESOURCE_ID:
        return device(resourceId=value).wait(timeout=timeout)
    elif selector_type == SelectorType.DESCRIPTION:
        return device(description=value).wait(timeout=timeout)
    elif selector_type == SelectorType.XPATH:
        return device.xpath(value).wait(timeout=timeout)
    else:
        logging.error(f"未知的选择器类型: {selector_type}")
        return False
