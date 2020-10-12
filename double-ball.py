#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import wx
import math
import sys
from datetime import datetime
from itertools import combinations, permutations

# TODO:
# - Fix using Chinese character (search FIXME)

g_version = "v1.0"
g_changelog = """
v0.5 (2019-04-08):
- 添加“打印”和“更新日志”按键
- 在选择胆码后保证数列按从小到大排列
- 窗口格局调整，输出窗口进一步变大
- 输出从一列调整为两列

v0.6 (2019-06-06):
- 将“首位奇偶”和“末尾奇偶”放到一行
- 胆码选择由选择改为输入数字
- 缩水结果显示修改：三列，每一列留有空隙，每五行留一空行，结果显示为[1] 01 02 03 ...
- 所有其他相关数字选择也用两位显示，如01，02，...
- 增加除4余0，1，2，3的选项

v0.7 (2019-12-14):
- 删除“和值范围”, “AC值”
- 允许缩水结果为6，8或者10个数字

v0.71 (2019-12-14):
- 修复“上期结果”总是6个数字

v0.72 (2019-12-15):
- 将输出结果由三列改为一列

v1.0 (2020-10-12):
- 改为分页面显示，并对原始约束条件进行分类
- 输出结果不显示序号
- 输出结果中每一个数字之间间隔4个空格
- 加入“除以5余数X”的5个附加缩水条件
- 对每一个约束条件增加“全选”和“清除”按钮
- 给标签增加颜色，当有选中参数时改变颜色
"""
g_title = "双色球缩水工具 - %s" % g_version
g_debug = True
g_prime_list = [1,2,3,5,7,11,13,17,19,23,29,31]
g_cross_list = [1,6,8,11,15,16,21,22,26,29,31]
g_outter_list = [1,2,3,4,5,6,7,12,13,18,19,24,25,30,31,32,33]
g_size = (1280, 700)
g_checkbox_size = (100, 40)
g_lastwin_size = (250, -1)
g_output_size = (1280, 500)
g_border = 3
g_border2 = 3
g_fontsize = 14
g_flag = wx.ALL | wx.EXPAND
g_elements = 6
g_result_columes = 1
g_color_enable = (255, 0, 0)
g_color_disable = (0, 255, 0)

# uncomment this to disable window resizing
# g_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
g_style = wx.DEFAULT_FRAME_STYLE

if sys.platform.startswith("linux"):
    g_os_windows = False
else:
    g_os_windows = True

if len(sys.argv) > 1:
    arg1 = sys.argv[1]
    if arg1.isdigit():
        val = int(arg1)
        if val in [6, 8, 10]:
            g_elements = val

class DBCore:
    """
    This is the core of the Double Ball program, which stores the main
    calculation logic of everything.
    """
    def __init__(self, outter_frame):
        self.outter_frame = outter_frame
        # Puts all the widgets
        self.items_others = []
        self.items_checkboxes = []
        self.items_buttons = []
        # Puts the results
        self.result = []
        self.result_str = ""
        #
        # static texts that may change bg color.  Formats:
        # [[static1, [checkbox1, ...], [static2, [checkbox2, ...]], ...]
        self.dynamic_statics = []
        # Init fonts
        if g_os_windows:
            self.font = wx.Font(wx.FontInfo(g_fontsize).Bold())
            self.font_small = wx.Font(wx.FontInfo(g_fontsize - 2).Bold())

    def do_setall_primes(self, event):
        for item in self.primes:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_primes(self, event):
        for item in self.primes:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_setall_conts(self, event):
        for item in self.conts:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_conts(self, event):
        for item in self.conts:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_setall_primes(self, event):
        for item in self.primes:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_primes(self, event):
        for item in self.primes:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_setall_odds(self, event):
        for item in self.odds:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_odds(self, event):
        for item in self.odds:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_setall_bigs(self, event):
        for item in self.bigs:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_bigs(self, event):
        for item in self.bigs:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_setall_diff_tails(self, event):
        for item in self.diff_tails:
            item.SetValue(True)
        self.refresh_static_texts()
    def do_clearall_diff_tails(self, event):
        for item in self.diff_tails:
            item.SetValue(False)
        self.refresh_static_texts()

    def do_quit(self, event):
        print("Quitting...")
        self.quit_app()

    def do_scan_checkboxes(self, event):
        self.refresh_static_texts()

    def refresh_static_texts(self):
        for entry in self.dynamic_statics:
            static, cb_list = entry
            enabled = False
            for cb in cb_list:
                if cb.GetValue():
                    enabled = True
                    break
            if enabled:
                static.SetBackgroundColour(g_color_enable)
            else:
                static.SetBackgroundColour(g_color_disable)

    def do_print(self, event):
        if not self.result:
            self.clear()
            self.out("请先进行一次成功的缩水！")
            return
        date = datetime.now()
        fname = "缩水结果-%s.txt" % date.strftime("%Y%m%d-%H%M%S")
        output = open(unicode(fname, "utf-8"), "w")
        output.write(self.result_str)
        output.close()
        self.out("缩水结果已保存到文件：'%s'" % fname)

    def do_changelog(self, event):
        self.clear()
        self.out(g_changelog.strip())

    def do_reset(self, event):
        self.clear()
        for box in self.items_checkboxes:
            box.SetValue(False)
        # self.sum_low.SetValue("")
        # self.sum_high.SetValue("")
        self.first_odd.SetSelection(-1)
        self.last_odd.SetSelection(-1)
        self.last_win.SetValue("")
        self.refresh_static_texts()
        self.out("所有参数已重置！")

    def apply_font(self):
        """Set font for all the widgets"""
        if g_os_windows:
            for item in self.items_others:
                item.SetFont(self.font)
            for item in self.items_checkboxes:
                item.SetFont(self.font)
            self.text_out.SetFont(self.font_small)

    def quit_app(self):
        self.outter_frame.Close()

    def valid(self, n):
        return n != -1 and n != []

    def count_prime_n(self, n_list):
        prime_cnt = 0
        for i in n_list:
            if i in g_prime_list:
                prime_cnt += 1
        return prime_cnt

    def count_odd_n(self, n_list):
        odds = 0
        for i in n_list:
            if i % 2:
                odds += 1
        return odds

    def count_sum(self, n_list):
        s = 0
        for i in n_list:
            s += i
        return s

    def count_ac(self, n_list):
        small_set = combinations(n_list, 2)
        result = []
        for i in small_set:
            v = abs(i[0] - i[1])
            if v not in result:
                result.append(v)
        return len(result) - len(n_list) + 1

    def count_diff_tail_n(self, n_list):
        result = []
        for i in n_list:
            tail = i % 10
            if tail not in result:
                result.append(tail)
        return len(result)

    def count_cross_n(self, n_list):
        result = 0
        for i in n_list:
            if i in g_cross_list:
                result += 1
        return result

    def count_outter_n(self, n_list):
        result = 0
        for i in n_list:
            if i in g_outter_list:
                result += 1
        return result

    def count_cont_n(self, n_list):
        cnt = 0
        for i in range(0, len(n_list)-1):
            if n_list[i] + 1 == n_list[i+1]:
                cnt += 1
        return cnt

    def count_big_n(self, n_list):
        cnt = 0
        for i in n_list:
            if i > 16:
                cnt += 1
        return cnt

    def count_three(self, n_list, rest):
        cnt = 0
        for i in n_list:
            if i % 3 == rest:
                cnt += 1
        return cnt

    def count_four(self, n_list, rest):
        cnt = 0
        for i in n_list:
            if i % 4 == rest:
                cnt += 1
        return cnt

    def count_five(self, n_list, rest):
        cnt = 0
        for i in n_list:
            if i % 5 == rest:
                cnt += 1
        return cnt

    def get_range(self, n):
        if n <= 11:
            return 0
        elif n <= 22:
            return 1
        else:
            return 2

    def count_range(self, n_list, rng):
        cnt = 0
        for i in n_list:
            if get_range(i) == rng:
                cnt += 1
        return cnt

    def count_last(self, n_list, last_win):
        cnt = 0
        for i in n_list:
            if i in last_win:
                cnt += 1
        return cnt

    def dball_calc(self, params):
        danma_list = params["danma_list"]
        num_list = params["num_list"]
        # set these parameters to -1 to disable the filtering
        prime_n = params["prime_n"]
        odd_n = params["odd_n"]
        big_n = params["big_n"]
        sum_low = params["sum_low"]
        sum_high = params["sum_high"]
        ac_val = params["ac_val"]
        diff_tail_n = params["diff_tail_n"]
        first_odd = params["first_odd"]
        last_odd = params["last_odd"]
        cross_n = params["cross_n"]
        outter_n = params["outter_n"]
        cont_n = params["cont_n"]
        three0 = params["three0"]
        three1 = params["three1"]
        three2 = params["three2"]
        four0 = params["four0"]
        four1 = params["four1"]
        four2 = params["four2"]
        four3 = params["four3"]
        five0 = params["five0"]
        five1 = params["five1"]
        five2 = params["five2"]
        five3 = params["five3"]
        five4 = params["five4"]
        range0 = params["range0"]
        range1 = params["range1"]
        range2 = params["range2"]
        last_win = params["last_win"]
        last_nums = params["last_nums"]

        rand_set = combinations(num_list, g_elements - len(danma_list))
        input_set = map(lambda x: x + tuple(danma_list), rand_set)
        output_set = []

        for array in input_set:
            array = list(array)
            # if there is any DanMa then sort them with the rest random ones
            array.sort()
            if self.valid(prime_n) and \
               self.count_prime_n(array) not in prime_n:
                continue
            if self.valid(big_n) and \
               self.count_big_n(array) not in big_n:
                continue
            if self.valid(odd_n) and \
               self.count_odd_n(array) not in odd_n:
                continue
            if self.valid(ac_val) and self.count_ac(array) not in ac_val:
                continue
            if self.valid(diff_tail_n) and \
               self.count_diff_tail_n(array) not in diff_tail_n:
                continue
            if self.valid(cross_n) and \
               self.count_cross_n(array) not in cross_n:
                continue
            if self.valid(outter_n) and \
               self.count_outter_n(array) not in outter_n:
                continue
            if self.valid(cont_n) and \
               self.count_cont_n(array) not in cont_n:
                continue

            if self.valid(three0) and \
               self.count_three(array, 0) not in three0:
                continue
            if self.valid(three1) and \
               self.count_three(array, 1) not in three1:
                continue
            if self.valid(three2) and \
               self.count_three(array, 2) not in three2:
                continue

            if self.valid(four0) and \
               self.count_four(array, 0) not in four0:
                continue
            if self.valid(four1) and \
               self.count_four(array, 1) not in four1:
                continue
            if self.valid(four2) and \
               self.count_four(array, 2) not in four2:
                continue
            if self.valid(four3) and \
               self.count_four(array, 3) not in four3:
                continue

            if self.valid(five0) and \
               self.count_five(array, 0) not in five0:
                continue
            if self.valid(five1) and \
               self.count_five(array, 1) not in five1:
                continue
            if self.valid(five2) and \
               self.count_five(array, 2) not in five2:
                continue
            if self.valid(five3) and \
               self.count_five(array, 3) not in five3:
                continue
            if self.valid(five4) and \
               self.count_five(array, 4) not in five4:
                continue

            if self.valid(range0) and \
               self.count_range(array, 0) not in range0:
                continue
            if self.valid(range1) and \
               self.count_range(array, 1) not in range1:
                continue
            if self.valid(range2) and \
               self.count_range(array, 2) not in range2:
                continue
            if self.valid(last_win) and self.valid(last_nums) and \
               self.count_last(array, last_win) not in last_nums:
                continue

            if self.valid(first_odd):
                odd = array[0] % 2
                if first_odd and not odd:
                    continue
                if not first_odd and odd:
                    continue
            if self.valid(last_odd):
                odd = array[-1] % 2
                if last_odd and not odd:
                    continue
                if not last_odd and odd:
                    continue

            sum_n = self.count_sum(array)
            if self.valid(sum_low) and sum_n < sum_low:
                continue
            if self.valid(sum_high) and sum_n > sum_high:
                continue

            output_set.append(array)

        return output_set

    def out(self, line, ret=True):
        if ret:
            line += "\n"
        self.text_out.AppendText(unicode(line, "utf-8"))

    def clear(self):
        self.text_out.SetValue("")

    def get_list_of_array(self, array, start_idx=0):
        # Get a list of numbers from an array of CheckBox.  The
        # start_idx is the offset number of returned list.
        result = []
        for i in range(0, len(array)):
            element = array[i]
            if element.GetValue():
                result.append(start_idx + i)
        return result

    def get_nums(self):
        return self.get_list_of_array(self.numbers, 1)

    def get_danma(self):
        return self.get_num_list(self.danma)

    def get_three0(self):
        return self.get_list_of_array(self.three0)
    def get_three1(self):
        return self.get_list_of_array(self.three1)
    def get_three2(self):
        return self.get_list_of_array(self.three2)

    def get_four0(self):
        return self.get_list_of_array(self.four0)
    def get_four1(self):
        return self.get_list_of_array(self.four1)
    def get_four2(self):
        return self.get_list_of_array(self.four2)
    def get_four3(self):
        return self.get_list_of_array(self.four3)

    def get_five0(self):
        return self.get_list_of_array(self.five0)
    def get_five1(self):
        return self.get_list_of_array(self.five1)
    def get_five2(self):
        return self.get_list_of_array(self.five2)
    def get_five3(self):
        return self.get_list_of_array(self.five3)
    def get_five4(self):
        return self.get_list_of_array(self.five4)

    def get_range0(self):
        return self.get_list_of_array(self.range0)

    def get_range1(self):
        return self.get_list_of_array(self.range1)

    def get_range2(self):
        return self.get_list_of_array(self.range2)

    def get_primes(self):
        return self.get_list_of_array(self.primes)

    def get_odds(self):
        return self.get_list_of_array(self.odds)

    def get_bigs(self):
        return self.get_list_of_array(self.bigs)

    def get_acs(self):
        return self.get_list_of_array(self.acs, 1)

    def get_diff_tails(self):
        return self.get_list_of_array(self.diff_tails, 3)

    def get_crosses(self):
        return self.get_list_of_array(self.crosses)

    def get_outters(self):
        return self.get_list_of_array(self.outters)

    def get_conts(self):
        return self.get_list_of_array(self.conts)

    def get_last_nums(self):
        return self.get_list_of_array(self.last_nums)

    def get_choice(self, item):
        value = item.GetSelection()
        if value == 0 or value == -1:
            return -1
        elif value == 1:
            return 1
        elif value == 2:
            return 0
        raise Exception("Unknown value: %s" % value)

    def get_num_list(self, item):
        """Item must be a textbox"""
        s = item.GetValue()
        if not s:
            result = []
        else:
            # non-null last win value, we will be strict
            try:
                s = s.decode("utf-8")
                s = s.replace(",", " ")
                s = s.replace(".", " ")
                s = s.replace("-", " ")
                s = s.replace(":", " ")
                s = s.replace("\\", " ")
                s = s.replace("/", " ")
                # FIXME: these are still not working
                s = s.replace("，".decode("utf-8"), " ")
                s = s.replace("、".decode("utf-8"), " ")
                s = s.replace("。".decode("utf-8"), " ")
                result = s.split()
                result = map(int, result)
                # sanity check
                for i in result:
                    if i > 33 or i <= 0:
                        raise Exception()
            except:
                result = -1
        return result

    def do_generate(self, event):
        self.clear()

        primes = self.get_primes()
        odds = self.get_odds()
        bigs = self.get_bigs()
        # acs = self.get_acs()
        diff_tails = self.get_diff_tails()
        crosses = self.get_crosses()
        outters = self.get_outters()
        first_odd = self.get_choice(self.first_odd)
        last_odd = self.get_choice(self.last_odd)
        conts = self.get_conts()
        
        three0 = self.get_three0()
        three1 = self.get_three1()
        three2 = self.get_three2()
        
        four0 = self.get_four0()
        four1 = self.get_four1()
        four2 = self.get_four2()
        four3 = self.get_four3()

        five0 = self.get_five0()
        five1 = self.get_five1()
        five2 = self.get_five2()
        five3 = self.get_five3()
        five4 = self.get_five4()
        
        range0 = self.get_range0()
        range1 = self.get_range1()
        range2 = self.get_range2()
        last_nums = self.get_last_nums()

        last_win = self.get_num_list(self.last_win)
        if type(last_win) != type([]):
            self.out("错误：上期结果解析错误，请重新输入")
            return
        if last_win and len(last_win) != 6:
            self.out("错误：上期结果必须是6个数字")
            return

        #
        # Get the values, report if there's error when parsing
        #
        danma = self.get_danma()
        if type(danma) != type([]):
            self.out("错误：胆码无法识别，请重新输入")
            return
        if len(danma) > 3:
            self.out("错误：胆码不能超过3个")
            return
        nums = self.get_nums()
        if len(danma) + len(nums) < g_elements:
            self.out("错误：请选择至少%s个备选数字" % (g_elements - len(danma)))
            return
        for n in danma:
            if n in nums:
                self.out("错误：不可同时选择胆码和备选数字(%s)" % n)
                return

        params = {
            "danma_list": danma,
            "num_list": nums,
            "prime_n": primes,
            "odd_n": odds,
            "big_n": bigs,
            "sum_low": -1, #sum_low,
            "sum_high": -1, #sum_high,
            "ac_val": [], #acs,
            "diff_tail_n": diff_tails,
            "first_odd": first_odd,
            "last_odd": last_odd,
            "cross_n": crosses,
            "outter_n": outters,
            "cont_n": conts,
            "three0": three0,
            "three1": three1,
            "three2": three2,
            "four0": four0,
            "four1": four1,
            "four2": four2,
            "four3": four3,
            "five0": five0,
            "five1": five1,
            "five2": five2,
            "five3": five3,
            "five4": five4,
            "range0": range0,
            "range1": range1,
            "range2": range2,
            "last_win": last_win,
            "last_nums": last_nums,
        }
        self.result = self.dball_calc(params)
        self.show_result(self.result)

    def show_result(self, result):
        full_line = "-" * 24 * g_result_columes
        self.out("缩水结果 (共 %s 个)：\n%s" % (len(result), full_line))
        if not result:
            self.result_str = ""
            self.out("未找到合适的结果，请修改缩水范围后重试。")
        else:
            start = 1
            result_str = "" 
            for entry in result:
                str_res = "    ".join(map(lambda x: "%02d" % x, entry))
                result_str += "%s" % str_res
                if start % g_result_columes:
                    result_str += " "
                else:
                    result_str += "\n"
                if start % 15 == 0:
                    result_str += full_line + "\n"
                start += 1
            self.result_str = result_str
            self.out(result_str)

class DBPanel(wx.Panel):
    """Parent class of all sub-panels"""
    def __init__(self, parent, core):
        wx.Frame.__init__(self, parent)
        # Points to the outter frame
        self.core = core

    def new_static(self, value, check_list=None):
        """Setup check_list to a list of checkboxes, so that the static will
        change background color if any of the checkbox is selected"""
        new = wx.StaticText(self, wx.ID_ANY, value)
        self.core.items_others.append(new)
        if check_list:
            entry = [new, check_list]
            self.core.dynamic_statics.append(entry)
        return new

    def new_checkbox(self, value):
        new = wx.CheckBox(self, wx.ID_ANY, value, size=g_checkbox_size)
        self.Bind(wx.EVT_CHECKBOX, self.core.do_scan_checkboxes, new)
        self.core.items_checkboxes.append(new)
        return new

    def new_button(self, value):
        new = wx.Button(self, wx.ID_ANY, value)
        self.core.items_buttons.append(new)
        return new

    def new_button_setall(self):
        return self.new_button("全选")
    def new_button_clearall(self):
        return self.new_button("清除")

    def bind_button(self, method, button):
        self.Bind(wx.EVT_BUTTON, method, button)

    def sizer_fill(self, sizer, n):
        while n:
            sizer.Add(self.new_static(""), flag=g_flag)
            n -= 1

class DBControlPanel(DBPanel):
    """The control panel"""
    def __init__(self, parent, core):
        DBPanel.__init__(self, parent, core)
        self.__create_objects()
        self.__do_layout()

    def __create_objects(self):
        self.core.text_out = wx.TextCtrl(self, wx.ID_ANY, "", size=g_output_size,
                                         style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.core.items_others.append(self.core.text_out)
        self.button_changelog = self.new_button("更新日志")
        self.button_print = self.new_button("输出结果")
        self.button_reset = self.new_button("重置参数")
        self.button_gen = self.new_button("生成结果")
        self.button_quit = self.new_button("退出")

        self.bind_button(self.core.do_generate, self.button_gen)
        self.bind_button(self.core.do_reset, self.button_reset)
        self.bind_button(self.core.do_quit, self.button_quit)
        self.bind_button(self.core.do_changelog, self.button_changelog)
        self.bind_button(self.core.do_print, self.button_print)

    def __do_layout(self):
        sizer_control = wx.FlexGridSizer(3, 1, 5, 5)
        sizer_control.Add(self.core.text_out, border=g_border, flag=g_flag)
        sizer_buttons1 = wx.GridSizer(1, 3, 5, 5)
        sizer_buttons2 = wx.GridSizer(1, 2, 5, 5)
        for button in [
                self.button_changelog,
                self.button_print,
                self.button_reset,
        ]:
            sizer_buttons1.Add(button, flag=g_flag, border=g_border)
        for button in [
                self.button_gen,
                self.button_quit,
        ]:
            sizer_buttons2.Add(button, flag=g_flag, border=g_border)
        sizer_control.Add(sizer_buttons1, border=g_border, flag=g_flag)
        sizer_control.Add(sizer_buttons2, border=g_border, flag=g_flag)
        self.SetSizer(sizer_control)

class DBModPanel(DBPanel):
    """除余页面"""
    def __init__(self, parent, core):
        DBPanel.__init__(self, parent, core)
        self.__create_objects()
        self.__do_layout()

    def __create_objects(self):
        # divide 3
        self.core.three0 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.three0.append(box)
        self.core.three1 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.three1.append(box)
        self.core.three2 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.three2.append(box)

        # divide 4
        self.core.four0 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.four0.append(box)
        self.core.four1 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.four1.append(box)
        self.core.four2 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.four2.append(box)
        self.core.four3 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.four3.append(box)

        # divide 5
        self.core.five0 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.five0.append(box)
        self.core.five1 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.five1.append(box)
        self.core.five2 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.five2.append(box)
        self.core.five3 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.five3.append(box)
        self.core.five4 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.five4.append(box)

    def __do_layout(self):
        sizer_conds = wx.FlexGridSizer(16, 2, 0, 0)

        sizer_three0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.three0:
            sizer_three0.Add(item, flag=g_flag)
        sizer_three1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.three1:
            sizer_three1.Add(item, flag=g_flag)
        sizer_three2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.three2:
            sizer_three2.Add(item, flag=g_flag)

        sizer_four0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.four0:
            sizer_four0.Add(item, flag=g_flag)
        sizer_four1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.four1:
            sizer_four1.Add(item, flag=g_flag)
        sizer_four2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.four2:
            sizer_four2.Add(item, flag=g_flag)
        sizer_four3 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.four3:
            sizer_four3.Add(item, flag=g_flag)

        sizer_five0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.five0:
            sizer_five0.Add(item, flag=g_flag)
        sizer_five1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.five1:
            sizer_five1.Add(item, flag=g_flag)
        sizer_five2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.five2:
            sizer_five2.Add(item, flag=g_flag)
        sizer_five3 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.five3:
            sizer_five3.Add(item, flag=g_flag)
        sizer_five4 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.five4:
            sizer_five4.Add(item, flag=g_flag)

        sizer_conds.Add(self.new_static("除3余0："))
        sizer_conds.Add(sizer_three0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除3余1："))
        sizer_conds.Add(sizer_three1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除3余2："))
        sizer_conds.Add(sizer_three2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static(""))
        sizer_conds.Add(self.new_static(""))
        sizer_conds.Add(self.new_static("除4余0："))
        sizer_conds.Add(sizer_four0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余1："))
        sizer_conds.Add(sizer_four1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余2："))
        sizer_conds.Add(sizer_four2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余3："))
        sizer_conds.Add(sizer_four3, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static(""))
        sizer_conds.Add(self.new_static(""))
        sizer_conds.Add(self.new_static("除5余0："))
        sizer_conds.Add(sizer_five0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除5余1："))
        sizer_conds.Add(sizer_five1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除5余2："))
        sizer_conds.Add(sizer_five2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除5余3："))
        sizer_conds.Add(sizer_five3, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除5余4："))
        sizer_conds.Add(sizer_five4, border=g_border, flag=g_flag)

        self.SetSizer(sizer_conds)

class DBPositionPanel(DBPanel):
    """位置参数"""
    def __init__(self, parent, core):
        DBPanel.__init__(self, parent, core)
        self.__create_objects()
        self.__do_layout()

    def __create_objects(self):
        self.core.outters = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.outters.append(box)

        self.core.range0 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.range0.append(box)
        self.core.range1 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.range1.append(box)
        self.core.range2 = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.range2.append(box)

        self.core.crosses = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.crosses.append(box)

    def __do_layout(self):
        sizer_conds = wx.FlexGridSizer(19, 2, 5, 5)
        sizer_outters = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for outter in self.core.outters:
            sizer_outters.Add(outter, flag=g_flag)
        sizer_range0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.range0:
            sizer_range0.Add(item, flag=g_flag)
        sizer_range1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.range1:
            sizer_range1.Add(item, flag=g_flag)
        sizer_range2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.core.range2:
            sizer_range2.Add(item, flag=g_flag)

        sizer_conds.Add(self.new_static("外围个数："))
        sizer_conds.Add(sizer_outters, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第一区间："))
        sizer_conds.Add(sizer_range0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第二区间："))
        sizer_conds.Add(sizer_range1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第三区间："))
        sizer_conds.Add(sizer_range2, border=g_border, flag=g_flag)

        sizer_crosses = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for cross in self.core.crosses:
            sizer_crosses.Add(cross, flag=g_flag)
        sizer_conds.Add(self.new_static("对角线："))
        sizer_conds.Add(sizer_crosses, border=g_border, flag=g_flag)

        self.SetSizer(sizer_conds)

class DBOtherPanel(DBPanel):
    """其他参数"""
    def __init__(self, parent, core):
        DBPanel.__init__(self, parent, core)
        self.__create_objects()
        self.__do_layout()

    def __create_objects(self):
        self.core.danma = wx.TextCtrl(self, wx.ID_ANY, "", size=g_lastwin_size)
        self.core.items_others.append(self.core.danma)
        self.core.last_win = wx.TextCtrl(self, wx.ID_ANY, "", size=g_lastwin_size)
        self.core.items_others.append(self.core.last_win)

        self.core.last_nums = []
        for i in range(0, 5):
            box = self.new_checkbox("%s" % i)
            self.core.last_nums.append(box)

        self.core.first_odd = wx.Choice(self, wx.ID_ANY,
                                        choices=["任意", "奇数", "偶数"])
        self.core.last_odd = wx.Choice(self, wx.ID_ANY,
                                       choices=["任意", "奇数", "偶数"])

    def __do_layout(self):
        sizer_danma_in = wx.FlexGridSizer(1, 2, 3, 3)
        sizer_danma_in.Add(self.core.danma, flag=g_flag)
        sizer_danma_in.Add(self.new_static("(例:01 02 03)"))

        sizer_conds_2 = wx.FlexGridSizer(12, 2, 5, 5)
        sizer_conds_2.Add(self.new_static("胆码选择："))
        sizer_conds_2.Add(sizer_danma_in, flag=g_flag)

        sizer_last_win = wx.FlexGridSizer(1, 2, g_border2, g_border2)
        sizer_last_win.Add(self.core.last_win, flag=g_flag)
        sizer_last_win.Add(self.new_static("(例:01 02 03 04 05 06)"))
        sizer_last_nums = wx.GridSizer(1, 5, 3, 3)
        for item in self.core.last_nums:
            sizer_last_nums.Add(item, flag=g_flag)

        sizer_conds_2.Add(self.new_static("上期结果："))
        sizer_conds_2.Add(sizer_last_win, border=g_border, flag=g_flag)
        sizer_conds_2.Add(self.new_static("上期重复："))
        sizer_conds_2.Add(sizer_last_nums, border=g_border, flag=g_flag)

        sizer_shoumojiou = wx.FlexGridSizer(1, 4, 0, 0)
        sizer_shoumojiou.Add(self.new_static("     "), flag=g_flag)
        sizer_shoumojiou.Add(self.core.first_odd, flag=g_flag)
        sizer_shoumojiou.Add(self.new_static("    末位奇偶：    "), flag=g_flag)
        sizer_shoumojiou.Add(self.core.last_odd, flag=g_flag)
        sizer_conds_2.Add(self.new_static("首位奇偶："))
        sizer_conds_2.Add(sizer_shoumojiou, flag=g_flag)

        self.SetSizer(sizer_conds_2)

class DBMainPanel(DBPanel):
    """主选参数"""
    def __init__(self, parent, core):
        DBPanel.__init__(self, parent, core)
        self.__create_objects()
        self.__do_layout()

    def __create_objects(self):
        # Including bindings of the objects (mostly, buttons)
        self.core.numbers = []
        for i in range(1, 34):
            box = self.new_checkbox("%02d" % i)
            self.core.numbers.append(box)

        self.core.primes = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s:%s" % (i, g_elements-i))
            self.core.primes.append(box)
        self.button_setall_primes = self.new_button_setall()
        self.button_clearall_primes = self.new_button_clearall()
        self.bind_button(self.core.do_setall_primes,
                         self.button_setall_primes)
        self.bind_button(self.core.do_clearall_primes,
                         self.button_clearall_primes)

        self.core.odds = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s:%s" % (i, g_elements-i))
            self.core.odds.append(box)
        self.button_setall_odds = self.new_button_setall()
        self.button_clearall_odds = self.new_button_clearall()
        self.bind_button(self.core.do_setall_odds,
                         self.button_setall_odds)
        self.bind_button(self.core.do_clearall_odds,
                         self.button_clearall_odds)

        self.core.bigs = []
        for i in range(0, g_elements + 1):
            box = self.new_checkbox("%s:%s" % (i, g_elements-i))
            self.core.bigs.append(box)
        self.button_setall_bigs = self.new_button_setall()
        self.button_clearall_bigs = self.new_button_clearall()
        self.bind_button(self.core.do_setall_bigs,
                         self.button_setall_bigs)
        self.bind_button(self.core.do_clearall_bigs,
                         self.button_clearall_bigs)

        self.core.diff_tails = []
        for i in range(3, g_elements + 1):
            box = self.new_checkbox("%s" % i)
            self.core.diff_tails.append(box)
        self.button_setall_diff_tails = self.new_button_setall()
        self.button_clearall_diff_tails = self.new_button_clearall()
        self.bind_button(self.core.do_setall_diff_tails,
                         self.button_setall_diff_tails)
        self.bind_button(self.core.do_clearall_diff_tails,
                         self.button_clearall_diff_tails)

        self.core.conts = []
        for i in range(0, g_elements):
            box = self.new_checkbox("%s" % i)
            self.core.conts.append(box)
        self.button_setall_conts = self.new_button_setall()
        self.button_clearall_conts = self.new_button_clearall()
        self.bind_button(self.core.do_setall_conts,
                         self.button_setall_conts)
        self.bind_button(self.core.do_clearall_conts,
                         self.button_clearall_conts)

    def __do_layout(self):
        # Most outter sizer
        sizer_all = wx.FlexGridSizer(1, 2, 5, 5)

        # 1st level
        sizer_conds = wx.FlexGridSizer(19, 2, 5, 5)
        sizer_right_all = wx.FlexGridSizer(1, 1, 5, 5)
        sizer_all.Add(sizer_conds, border=g_border, flag=g_flag)
        sizer_all.Add(sizer_right_all, border=g_border, flag=g_flag)

        # Conditions REGION
        sizer_numbers_in = wx.GridSizer(4, 9, g_border2, g_border2)
        for num in self.core.numbers:
            sizer_numbers_in.Add(num, flag=g_flag)

        sizer_primes = wx.GridSizer(1, g_elements + 3, g_border2, g_border2)
        for prime in self.core.primes:
            sizer_primes.Add(prime, flag=g_flag)
        sizer_primes.Add(self.button_setall_primes, flag=g_flag)
        sizer_primes.Add(self.button_clearall_primes, flag=g_flag)
        sizer_odds = wx.GridSizer(1, g_elements + 3, g_border2, g_border2)
        for odd in self.core.odds:
            sizer_odds.Add(odd, flag=g_flag)
        sizer_odds.Add(self.button_setall_odds, flag=g_flag)
        sizer_odds.Add(self.button_clearall_odds, flag=g_flag)
        sizer_bigs = wx.GridSizer(1, g_elements + 3, g_border2, g_border2)
        for big in self.core.bigs:
            sizer_bigs.Add(big, flag=g_flag)
        sizer_bigs.Add(self.button_setall_bigs, flag=g_flag)
        sizer_bigs.Add(self.button_clearall_bigs, flag=g_flag)
        sizer_acs = wx.GridSizer(2, 5, g_border2, g_border2)

        sizer_diff_tails = wx.GridSizer(1, g_elements + 3, g_border2, g_border2)
        for tail in self.core.diff_tails:
            sizer_diff_tails.Add(tail, flag=g_flag)
        self.sizer_fill(sizer_diff_tails, 3);
        sizer_diff_tails.Add(self.button_setall_diff_tails, flag=g_flag)
        sizer_diff_tails.Add(self.button_clearall_diff_tails, flag=g_flag)

        sizer_conts = wx.GridSizer(1, g_elements + 3, g_border2, g_border2)
        for cont in self.core.conts:
            sizer_conts.Add(cont, flag=g_flag)
        self.sizer_fill(sizer_conts, 1);
        sizer_conts.Add(self.button_setall_conts, flag=g_flag)
        sizer_conts.Add(self.button_clearall_conts, flag=g_flag)

        sizer_conds.Add(self.new_static("数字选择：", self.core.numbers))
        sizer_conds.Add(sizer_numbers_in, flag=g_flag)
        sizer_conds.Add(self.new_static("质合比：", self.core.primes))
        sizer_conds.Add(sizer_primes, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("大小比：", self.core.bigs))
        sizer_conds.Add(sizer_bigs, border=g_border, flag=g_flag)

        sizer_conds.Add(self.new_static("连号个数：", self.core.conts))
        sizer_conds.Add(sizer_conts, border=g_border, flag=g_flag)

        sizer_conds.Add(self.new_static("不同尾数：", self.core.diff_tails))
        sizer_conds.Add(sizer_diff_tails, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("奇偶比：", self.core.odds))
        sizer_conds.Add(sizer_odds, border=g_border, flag=g_flag)

        self.SetSizer(sizer_all)

class MyApp(wx.App):
    def OnInit(self):
        outter_frame = wx.Frame(None, wx.ID_ANY, 
                                g_title, size=g_size)
        core = DBCore(outter_frame)
        outter_panel = wx.Panel(outter_frame)
        notebook = wx.Notebook(outter_panel)
        notebook.SetPageSize(g_size)

        # connect notebook to outter_panel
        sizer = wx.FlexGridSizer(2, 1, 5, 5)
        sizer.Add(notebook, g_flag, 5)
        outter_panel.SetSizer(sizer)

        # connect notebook with major frame
        main_panel = DBMainPanel(notebook, core)
        mod_panel = DBModPanel(notebook, core)
        position_panel = DBPositionPanel(notebook, core)
        other_panel = DBOtherPanel(notebook, core)
        control_panel = DBControlPanel(notebook, core)
        notebook.AddPage(main_panel, "主选参数")
        notebook.AddPage(mod_panel, "除余参数")
        notebook.AddPage(position_panel, "位置参数")
        notebook.AddPage(other_panel, "其他参数")
        notebook.AddPage(control_panel, "控制页面")

        # Change fonts for all widgets
        core.apply_font()

        if g_debug:
            for i in range(1, 10):
                core.numbers[i-1].SetValue(True)
        core.refresh_static_texts()

        self.SetTopWindow(outter_frame)
        outter_frame.Layout()
        outter_frame.Show()

        return True

if __name__ == "__main__":
    double_ball = MyApp(0)
    double_ball.MainLoop()
