# coding:utf-8
import ConfigParser
import Queue
import datetime
import linecache
import logging
import logging.handlers
import multiprocessing
import os
import psutil
import re
import smtplib
import sys
import threading
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import ntplib
import serial
import threadpool
from PyQt4 import QtGui, QtCore
from UI_Auto_Check_Log import Ui_Auto_Check_Log


class Main(Ui_Auto_Check_Log, threading.Thread, QtGui.QWidget):
    def __init__(self, parent=None):
        threading.Thread.__init__(self, parent)
        QtGui.QWidget.__init__(self)
        self.setupUi(self)
        self.setFixedSize(1102, 712)

        self.qt_obj = QtCore.QObject()

        self.tBserial_log.document().setMaximumBlockCount(100)  # 限制最大行数
        self.textBrowser.document().setMaximumBlockCount(100000)  # 限制最大行数

        self.connect(self.qt_obj, QtCore.SIGNAL("NewData"), self.show_serial_data)  # 建立槽函数，监听串口输出
        self.connect(self.qt_obj, QtCore.SIGNAL("Error"), self.close_script)  # 建立槽函数，串口占用处理函数

        self.num = 0
        self.f_time_pid = f_time_pid
        self.request = []  # 创建线程池
        self.pool = threadpool.ThreadPool(2)
        self.pool.wait()

        self.line_num_front = 5  # 设置匹配log相关个数

        line_num_all = self.line_num_front + 2  # 设置消息队列最大个数
        self.line_num_all = line_num_all
        self.queue_flag = None  # 匹配log的消息队列标志位
        self.show_serial_data_queue = Queue.Queue()
        self.check_log_count_queue = Queue.Queue()
        self.send_mail_queue = Queue.Queue()

        self.button_conf = 0  # 按钮标志位
        self.on_off_flag = "online"  # 设备在线状态标志位

        # UI显示初始化
        self.serial_com = ""  # 串口
        self.serial_baud = ""  # 波特率
        self.serial_mac = ""  # MAC地址
        self.serial_name = ""  # log文件名称范例
        self.serial_model = ""  # 设备型号
        self.LOG_PATH_FILE = ""  # log文件名称

        self.serial_sever = None
        self.all_log_data = None
        self.queue_put_num = 0

        # UI控件显示集初始化
        check_log_name_list = [[self.lEcheck_flag_0, self.lEcheck_num_0], [self.lEcheck_flag_1, self.lEcheck_num_1],
                               [self.lEcheck_flag_2, self.lEcheck_num_2], [self.lEcheck_flag_3, self.lEcheck_num_3],
                               [self.lEcheck_flag_4, self.lEcheck_num_4], [self.lEcheck_flag_5, self.lEcheck_num_5],
                               [self.lEcheck_flag_6, self.lEcheck_num_6], [self.lEcheck_flag_7, self.lEcheck_num_7],
                               [self.lEcheck_flag_8, self.lEcheck_num_8], [self.lEcheck_flag_9, self.lEcheck_num_9],
                               [self.lEbaud, None], [self.lEdevice_model, None], [self.lEmac, None]]
        num_list = [i for i in (xrange(len(check_log_name_list)))]
        self.check_log_name_dict = dict(zip(num_list, check_log_name_list))
        # dict.fromkeys(num_list,check_log_name_list) # 列表批量转字典

        # 串口读取相关初始化
        self.serial_check_flag_0 = ""
        self.serial_check_flag_1 = ""
        self.serial_check_flag_2 = ""
        self.serial_check_flag_3 = ""
        self.serial_check_flag_4 = ""
        self.serial_check_flag_5 = ""
        self.serial_check_flag_6 = ""
        self.serial_check_flag_7 = ""
        self.serial_check_flag_8 = ""
        self.serial_check_flag_9 = ""

        self.serial_num_0 = 0
        self.serial_num_1 = 0
        self.serial_num_2 = 0
        self.serial_num_3 = 0
        self.serial_num_4 = 0
        self.serial_num_5 = 0
        self.serial_num_6 = 0
        self.serial_num_7 = 0
        self.serial_num_8 = 0
        self.serial_num_9 = 0

        self.space_distance_0 = 0
        self.space_distance_1 = 0
        self.space_distance_2 = 0
        self.space_distance_3 = 0
        self.space_distance_4 = 0
        self.space_distance_5 = 0
        self.space_distance_6 = 0
        self.space_distance_7 = 0
        self.space_distance_8 = 0
        self.space_distance_9 = 0

        self.len_serial_num_0 = 1
        self.len_serial_num_1 = 1
        self.len_serial_num_2 = 1
        self.len_serial_num_3 = 1
        self.len_serial_num_4 = 1
        self.len_serial_num_5 = 1
        self.len_serial_num_6 = 1
        self.len_serial_num_7 = 1
        self.len_serial_num_8 = 1
        self.len_serial_num_9 = 1

        serial_check_flag_list = [
            [self.serial_check_flag_0, self.serial_num_0, self.space_distance_0, self.len_serial_num_0],
            [self.serial_check_flag_1, self.serial_num_1, self.space_distance_1, self.len_serial_num_1],
            [self.serial_check_flag_2, self.serial_num_2, self.space_distance_2, self.len_serial_num_2],
            [self.serial_check_flag_3, self.serial_num_3, self.space_distance_3, self.len_serial_num_3],
            [self.serial_check_flag_4, self.serial_num_4, self.space_distance_4, self.len_serial_num_4],
            [self.serial_check_flag_5, self.serial_num_5, self.space_distance_5, self.len_serial_num_5],
            [self.serial_check_flag_6, self.serial_num_6, self.space_distance_6, self.len_serial_num_6],
            [self.serial_check_flag_7, self.serial_num_7, self.space_distance_7, self.len_serial_num_7],
            [self.serial_check_flag_8, self.serial_num_8, self.space_distance_8, self.len_serial_num_8],
            [self.serial_check_flag_9, self.serial_num_9, self.space_distance_9, self.len_serial_num_9]]
        num_list = [i for i in (xrange(len(serial_check_flag_list)))]
        self.serial_check_flag_dict = dict(zip(num_list, serial_check_flag_list))

        # 消息队列相关初始化
        call_addr_flag_list = [[Queue.Queue(line_num_all), "queue_0"], [Queue.Queue(line_num_all), "queue_1"],
                               [Queue.Queue(line_num_all), "queue_2"], [Queue.Queue(line_num_all), "queue_3"],
                               [Queue.Queue(line_num_all), "queue_4"], [Queue.Queue(line_num_all), "queue_5"],
                               [Queue.Queue(line_num_all), "queue_6"], [Queue.Queue(line_num_all), "queue_7"],
                               [Queue.Queue(line_num_all), "queue_8"], [Queue.Queue(line_num_all), "queue_9"]]
        num_list = [i for i in (xrange(len(call_addr_flag_list)))]
        self.call_addr_flag_dict = dict(zip(num_list, call_addr_flag_list))

        focus_flag_0 = "None"
        focus_flag_1 = "None"
        focus_flag_2 = "None"
        focus_flag_3 = "None"
        focus_flag_4 = "None"
        focus_flag_5 = "None"
        focus_flag_6 = "None"
        focus_flag_7 = "None"
        focus_flag_8 = "None"
        focus_flag_9 = "None"

        focus_log_list = [focus_flag_0, focus_flag_1, focus_flag_2, focus_flag_3, focus_flag_4,
                          focus_flag_5, focus_flag_6, focus_flag_7, focus_flag_8, focus_flag_9]
        num_list = [i for i in (xrange(len(focus_log_list)))]
        self.focus_log_dict = dict(zip(num_list, focus_log_list))

        # 读取配置文件并在UI显示
        self.read_conf = ConfigParser.ConfigParser()
        self.read_conf.read("AutoCheckLog.ini")
        self.secs = self.read_conf.sections()
        opts = self.read_conf.options(self.secs[0])
        self.device_conf = self.read_conf.options(self.secs[1])
        self.send_mail_addr = self.read_conf.options(self.secs[2])
        self.info = opts
        for No, name in self.check_log_name_dict.items():
            if No < 10:
                name[0].setText(self.read_conf.get(self.secs[0], opts[No]))  # 显示在UI界面
            else:
                opts = self.read_conf.options(self.secs[1])
                name[0].setText(self.read_conf.get(self.secs[1], opts[No - 10]))  # 显示在UI界面
        self.lEmail.setText(self.read_conf.get(self.secs[2], self.send_mail_addr[0]))

    # 初始化log保存格式
    def init_log_save_mode(self):
        self.LOG_PATH_FILE = "GN-%s-%s-%s-" % (self.serial_model, self.on_off_flag, self.serial_mac)  # log文件名称

        # log文件保存格式
        logging.basicConfig(level=logging.INFO)  # 设置打印级别
        log_mode = 'midnight'  # 'midnight' #设置每天凌晨0点拆分log文件，可设置任意时间单位秒，分，时，天，周，月，年
        log_interval = 1  # 时间单位的参数，此处为1天
        log_max_files = 0  # 最大保存文件个数，0代表无限制
        fmt_str = '%(message)s'  # log文件写入内容，此处为正文
        files_handle = logging.handlers.TimedRotatingFileHandler(self.LOG_PATH_FILE, log_mode, log_interval,
                                                                 log_max_files)
        files_handle.suffix = "[%Y-%m-%d_%H-%M-%S].log"  # 保存log文件名称格式
        # 此处改了suffix源文件345行
        formatter = logging.Formatter(fmt_str)
        files_handle.setFormatter(formatter)
        logging.getLogger('').addHandler(files_handle)  # 初始化完毕

    # 串口被占用时关闭脚本
    def close_script(self):
        QtGui.QMessageBox.warning(self, "warning", u"串口打开失败，请检查串口是否被占用或串口选择错误！", "")
        self.pBbegin.setText(u"开始")

    # 读取匹配log的文件内容
    def read_tmp_logfile(self, file_name):
        log_tmp = ""
        try:
            linecache.checkcache("%s.log" % file_name)  # 将文件更新至最新
            with open("%s.log" % file_name, "r") as log:
                try:
                    log_tmp = log.read()
                finally:
                    log.close()
        except IOError:
            pass
        return log_tmp

    # 开始运行脚本
    def script_start(self):
        if self.pBbegin.text() == u"保存log":
            self.pBbegin.setText(u"暂停")
            self.result_report()  # 输出结果报告
            try:
                logging.shutdown()
                file_time = datetime.datetime.now().strftime('[%Y-%m-%d_%H-%M-%S]')
                os.rename(self.LOG_PATH_FILE, "%s%s.log" % (self.LOG_PATH_FILE, file_time))  # 将缓存文件换成正式文件
            except WindowsError:
                pass
        else:
            self.pBbegin.setText(u"保存log")

            self.request.append(threadpool.makeRequests(self.receive_log, [""])[0])  # 创建线程池任务列表
            self.pool.putRequest(self.request[0])  # 将任务推入任务队列中
            self.request.pop(0)  # 删除列表中已创建的任务

    # 读取串口log
    def receive_log(self, key):
        self.serial_com = str(self.cBcom.currentText())
        try:
            self.serial_sever = serial.Serial(self.serial_com, self.serial_baud, timeout=1)  # 串口参数初始化
            if self.button_conf == 0:
                self.init_log_save_mode()  # 初始化log保存格式
                self.button_conf = 1  # 只能初始化一次
            while 1:
                try:
                    if self.pBbegin.text() != u"暂停":
                        data = self.serial_sever.readline()  # 读取数据
                        if data is '':
                            data = "there is no log"
                            data_time = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S:%f]')
                            data = "%s%s" % (data_time, data)

                            self.show_serial_data_queue.put_nowait(data)  # data推入UI显示的消息队列中
                            self.check_log_count_queue.put_nowait(data)  # data推入数据统计的队列中

                            self.qt_obj.emit(QtCore.SIGNAL("NewData"), data)  # 串口数据变动抛出信号

                            logging.info(data)
                            continue

                        data = data.strip()
                        data_time = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S:%f]')
                        data = "%s%s" % (data_time, data)

                        self.show_serial_data_queue.put_nowait(data)  # data推入UI显示的消息队列中
                        self.check_log_count_queue.put_nowait(data)  # data推入数据统计的队列中

                        self.qt_obj.emit(QtCore.SIGNAL("NewData"), data)  # 串口数据变动抛出信号

                        logging.info(data)  # 打印log
                    else:
                        self.serial_sever.close()  # 关闭串口
                        if not self.serial_sever.isOpen():  # 检测串口是否已经关闭
                            break  # 跳出
                except AttributeError:
                    break
        except serial.serialutil.SerialException:
            self.qt_obj.emit(QtCore.SIGNAL("Error"), "")  # 串口打开失败抛出信号

    # 串口log进入的serial_queue消息队列在此处出列，并显示到UI界面上栏
    def show_serial_data(self):
        try:
            serial_log_queue = self.show_serial_data_queue.get_nowait()  # 出列
            self.tBserial_log.append(serial_log_queue)  # 打印到UI
        except Queue.Empty:
            pass

    '''
    UI界面上栏数据发生变化调用record_data，发现匹配log显示到UI界面下栏
    同时统计出现次数，并显示。
    创建10个匹配log的消息队列用于存储上文log
    '''

    def record_data(self):
        try:
            all_log_data = self.check_log_count_queue.get_nowait()  # 开始消费数据

            # 将串口数据又推入到10个匹配log单独的消息队列中
            for No, name in self.call_addr_flag_dict.items():
                name[0].put_nowait(all_log_data)
                if name[0].qsize() == self.line_num_all:
                    name[0].get_nowait()  # 超过限制即销毁

            # 发现串口数据中含有待检测的数据即开始处理
            for No, name in self.check_log_name_dict.items():
                if No == 10:  # self.check_log_name_dict参数超过10个做限制
                    break
                elif self.serial_check_flag_dict[No][0] == "":  # 清除空的匹配log
                    pass
                elif self.serial_check_flag_dict[No][0] in all_log_data:  # 出现匹配log
                    self.send_mail_queue.put_nowait(all_log_data)
                    self.serial_check_flag_dict[No][1] += 1  # 出现次数+1
                    self.textBrowser.append(all_log_data)  # UI显示
                    self.queue_flag = self.call_addr_flag_dict[No][1]  # 填入匹配log消息队列的标志位
                    name[1].setText(str(self.serial_check_flag_dict[No][1]))  # UI显示

                    self.request.append(threadpool.makeRequests(
                        self.write_report, [[self.queue_flag, self.serial_check_flag_dict[No][0], No]])[0])  # 线程池
                    self.pool.putRequest(self.request[0])
                    self.request.pop(0)

            feedid = re.findall(r"JOYLINK_FEEDID=(\d+)", all_log_data)[0]
            self.lEfeedid.setText(feedid)
        except Queue.Empty:
            pass
        except IndexError:
            pass

    # 写入匹配log的log文件
    def write_report(self, key):
        if self.queue_flag == key[0]:
            matching_log_line_num = self.line_num_all  # 写入匹配log的前5行
            with open("%s.log" % key[1], "a") as logfile:
                try:
                    logfile.write("%s\n" % ("*" * 173))
                    while matching_log_line_num > 1:
                        serial_log = self.call_addr_flag_dict[key[2]][0].get_nowait() + "\n"
                        logfile.write(serial_log)
                        matching_log_line_num -= 1
                except Queue.Empty:
                    pass
                finally:
                    logfile.close()

    # 输出结果报告
    def result_report(self):
        while 1:
            try:
                for No, name in self.serial_check_flag_dict.items():
                    print No, name
                    tmp = len(str(name[1]))
                    if name[3] is not tmp:  # 统计数字长度发生变化 从1变成10
                        self.serial_check_flag_dict[No][2] = tmp - 1  # 间距-1
                with open("Equipment_action.log", "r+") as logfile:
                    logfile.seek(0)  # 在文件开头插入
                    try:
                        # 结果报告的格式，用*号隔离
                        check_log = "&检查的log "
                        check_log_count = "&次数(次)  "

                        # 页眉包括匹配log的名称和具体统计数据
                        for No, name in self.serial_check_flag_dict.items():
                            check_log = "%s[%s]   " % (check_log, name[0])
                            check_log_count = "%s[%s]%s" % (
                                check_log_count, name[1], " " * (len(name[0]) - name[2] + 2))

                        check_log_num = len(check_log)
                        check_log = "%s&\n" % check_log
                        check_log_count = "%s&" % check_log_count
                        check_log_count_num = len(check_log_count) + 1

                        # 写入报告的页眉，统计数据
                        logfile.write("%s\n" % ("&" * (check_log_num - 4)))
                        logfile.write(check_log)
                        logfile.write("%s%s\n" % (check_log_count, "&" * (check_log_num - check_log_count_num)))
                        logfile.write("%s\n" % ("&" * (check_log_num - 4)))

                        # 写入报告的正文，所有log数据
                        for No, name in self.serial_check_flag_dict.items():
                            logfile.write(self.read_tmp_logfile(name[0]))
                            try:
                                os.remove("%s.log" % name[0])  # 写入完毕删除文件
                            except WindowsError:
                                pass
                    finally:
                        logfile.close()
                        break
            except IOError:
                with open("Equipment_action.log", "w") as logfile:  # 没有该文件就创建该文件
                    try:
                        pass
                    finally:
                        logfile.close()

    def record_log(self):
        data = self.send_mail_queue.get_nowait()
        for No, name in self.focus_log_dict.items():
            if name in data:
                count = int(self.serial_check_flag_dict[No][1])
                if count == 4:
                    self.request.append(threadpool.makeRequests(self.send_mail, [[name, count]])[0])  # 线程池
                    self.pool.putRequest(self.request[0])
                    self.request.pop(0)


class UiShow(Main):
    def format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr(
            (Header(name, 'utf-8').encode(), addr.encode('utf-8') if isinstance(addr, unicode) else addr))

    def send_mail(self, key):
        from_addr = ""
        password = ""
        to_addr = str(self.lEmail.text())
        smtp_server = "smtp.163.com"

        msg = MIMEText('告警！设备出现 <%s %s次> ！\n请及时查看设备状态！！' % (key[0], key[1]), 'plain', 'utf-8')
        msg['From'] = self.format_addr(u'自动检查log脚本客户端 <%s>' % from_addr)
        msg['To'] = self.format_addr(u'管理员 <%s>' % to_addr)
        msg['Subject'] = Header(u'自动检查log脚本自动告警', 'utf-8').encode()

        server = smtplib.SMTP(smtp_server, 25)
        server.set_debuglevel(1)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()

    def check_on_off(self):
        if self.ckBonoff.isChecked():
            self.ckBonoff.setText(u"离线")
            self.on_off_flag = "offline"
        else:
            self.ckBonoff.setText(u"在线")
            self.on_off_flag = "online"

    def closeEvent(self, QCloseEvent):
        try:
            psutil.Process(self.f_time_pid).kill()
            if self.serial_sever.isOpen():
                reply = QtGui.QMessageBox.question(self, 'Message', u"是否要断开串口?", QtGui.QMessageBox.Yes,
                                                   QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                    self.serial_sever.close()  # 关闭串口
                    self.result_report()  # 写报告
                    try:
                        logging.shutdown()
                        file_time = datetime.datetime.now().strftime('[%Y-%m-%d_%H-%M-%S]')
                        os.rename(self.LOG_PATH_FILE, "%s%s.log" % (self.LOG_PATH_FILE, file_time))
                    except WindowsError:
                        pass
                else:
                    QCloseEvent.ignore()
            else:
                psutil.Process(self.f_time_pid).kill()
        except AttributeError:
            psutil.Process(self.f_time_pid).kill()

    def text_change_0(self):
        flag = 0
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_1(self):
        flag = 1
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_2(self):
        flag = 2
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_3(self):
        flag = 3
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_4(self):
        flag = 4
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_5(self):
        flag = 5
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_6(self):
        flag = 6
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_7(self):
        flag = 7
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_8(self):
        flag = 8
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_9(self):
        flag = 9
        text = str(self.check_log_name_dict[flag][0].text())
        self.check_log_name_dict[flag][0].setText(text)
        self.serial_check_flag_dict[flag][0] = text
        self.read_conf.set(self.secs[0], self.info[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_baud(self):
        flag = 0
        text = str(self.check_log_name_dict[flag + 10][0].text())
        self.serial_baud = int(text)  # 波特率
        self.check_log_name_dict[flag + 10][0].setText(text)
        self.read_conf.set(self.secs[1], self.device_conf[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_model(self):
        flag = 1
        text = str(self.check_log_name_dict[flag + 10][0].text())
        self.serial_model = text  # 设备型号
        self.check_log_name_dict[flag + 10][0].setText(text)
        self.read_conf.set(self.secs[1], self.device_conf[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_mac(self):
        flag = 2
        text = str(self.check_log_name_dict[flag + 10][0].text())
        self.serial_mac = text  # MAC地址
        self.check_log_name_dict[flag + 10][0].setText(text)
        self.read_conf.set(self.secs[1], self.device_conf[flag], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def text_change_mail(self):
        text = str(self.lEmail.text())  # Mail地址
        self.read_conf.set(self.secs[2], self.send_mail_addr[0], text)
        self.read_conf.write(open("AutoCheckLog.ini", "w"))

    def clear_num_0(self):
        self.serial_check_flag_dict[0][1] = 0
        self.lEcheck_num_0.setText("")

    def clear_num_1(self):
        self.serial_check_flag_dict[1][1] = 0
        self.lEcheck_num_1.setText("")

    def clear_num_2(self):
        self.serial_check_flag_dict[2][1] = 0
        self.lEcheck_num_2.setText("")

    def clear_num_3(self):
        self.serial_check_flag_dict[3][1] = 0
        self.lEcheck_num_3.setText("")

    def clear_num_4(self):
        self.serial_check_flag_dict[4][1] = 0
        self.lEcheck_num_4.setText("")

    def clear_num_5(self):
        self.serial_check_flag_dict[5][1] = 0
        self.lEcheck_num_5.setText("")

    def clear_num_6(self):
        self.serial_check_flag_dict[6][1] = 0
        self.lEcheck_num_6.setText("")

    def clear_num_7(self):
        self.serial_check_flag_dict[7][1] = 0
        self.lEcheck_num_7.setText("")

    def clear_num_8(self):
        self.serial_check_flag_dict[8][1] = 0
        self.lEcheck_num_8.setText("")

    def clear_num_9(self):
        self.serial_check_flag_dict[9][1] = 0
        self.lEcheck_num_9.setText("")

    def focus_log_0(self):
        flag = 0
        if self.ckB_0.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_1(self):
        flag = 1
        if self.ckB_1.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_2(self):
        flag = 2
        if self.ckB_2.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_3(self):
        flag = 3
        if self.ckB_3.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_4(self):
        flag = 4
        if self.ckB_4.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_5(self):
        flag = 5
        if self.ckB_5.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_6(self):
        flag = 6
        if self.ckB_6.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_7(self):
        flag = 7
        if self.ckB_7.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_8(self):
        flag = 8
        if self.ckB_8.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"

    def focus_log_9(self):
        flag = 9
        if self.ckB_9.isChecked():
            self.focus_log_dict[flag] = self.serial_check_flag_dict[flag][0]
        else:
            self.focus_log_dict[flag] = "None"


def fix_sys_time(q):
    q.put(os.getpid())
    while True:
        try:
            ts = ntplib.NTPClient().request('cn.pool.ntp.org').tx_time
            _date = time.strftime('%Y-%m-%d', time.localtime(ts))
            _time = time.strftime('%X', time.localtime(ts))
            os.system('date {} && time {}'.format(_date, _time))
            time.sleep(1800)
        except:
            pass


f_time_pid = 0
if __name__ == "__main__":
    q = multiprocessing.Queue()
    f_time = multiprocessing.Process(target=fix_sys_time, args=(q,))
    f_time.start()
    f_time_pid = q.get()
    app = QtGui.QApplication(sys.argv)
    my = UiShow()
    my.show()
    sys.exit(app.exec_())
