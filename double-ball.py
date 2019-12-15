#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import wx
import math
import sys
from datetime import datetime
from itertools import combinations, permutations

# TODO:
# - Fix using Chinese character (search FIXME)

g_version = "v0.71"
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
"""
g_title = "双色球缩水工具 - %s" % g_version
g_debug = False
g_prime_list = [1,2,3,5,7,11,13,17,19,23,29,31]
g_cross_list = [1,6,8,11,15,16,21,22,26,29,31]
g_outter_list = [1,2,3,4,5,6,7,12,13,18,19,24,25,30,31,32,33]
g_size = (1280, 700)
g_lastwin_size = (250, -1)
g_output_size = (800, 300)
g_border = 3
g_border2 = 3
g_fontsize = 14
g_flag = wx.ALL | wx.EXPAND
g_elements = 8

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

def valid(n):
    return n != -1 and n != []

def count_prime_n(n_list):
    prime_cnt = 0
    for i in n_list:
        if i in g_prime_list:
            prime_cnt += 1
    return prime_cnt

def count_odd_n(n_list):
    odds = 0
    for i in n_list:
        if i % 2:
            odds += 1
    return odds

def count_sum(n_list):
    s = 0
    for i in n_list:
        s += i
    return s

def count_ac(n_list):
    small_set = combinations(n_list, 2)
    result = []
    for i in small_set:
        v = abs(i[0] - i[1])
        if v not in result:
            result.append(v)
    return len(result) - len(n_list) + 1

def count_diff_tail_n(n_list):
    result = []
    for i in n_list:
        tail = i % 10
        if tail not in result:
            result.append(tail)
    return len(result)

def count_cross_n(n_list):
    result = 0
    for i in n_list:
        if i in g_cross_list:
            result += 1
    return result

def count_outter_n(n_list):
    result = 0
    for i in n_list:
        if i in g_outter_list:
            result += 1
    return result

def count_cont_n(n_list):
    cnt = 0
    for i in range(0, len(n_list)-1):
        if n_list[i] + 1 == n_list[i+1]:
            cnt += 1
    return cnt

def count_big_n(n_list):
    cnt = 0
    for i in n_list:
        if i > 16:
            cnt += 1
    return cnt

def count_three(n_list, rest):
    cnt = 0
    for i in n_list:
        if i % 3 == rest:
            cnt += 1
    return cnt

def count_four(n_list, rest):
    cnt = 0
    for i in n_list:
        if i % 4 == rest:
            cnt += 1
    return cnt

def get_range(n):
    if n <= 11:
        return 0
    elif n <= 22:
        return 1
    else:
        return 2

def count_range(n_list, rng):
    cnt = 0
    for i in n_list:
        if get_range(i) == rng:
            cnt += 1
    return cnt

def count_last(n_list, last_win):
    cnt = 0
    for i in n_list:
        if i in last_win:
            cnt += 1
    return cnt

def dball_calc(params):
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
        if valid(prime_n) and count_prime_n(array) not in prime_n:
            continue
        if valid(big_n) and count_big_n(array) not in big_n:
            continue
        if valid(odd_n) and count_odd_n(array) not in odd_n:
            continue
        if valid(ac_val) and count_ac(array) not in ac_val:
            continue
        if valid(diff_tail_n) and count_diff_tail_n(array) not in diff_tail_n:
            continue
        if valid(cross_n) and count_cross_n(array) not in cross_n:
            continue
        if valid(outter_n) and count_outter_n(array) not in outter_n:
            continue
        if valid(cont_n) and count_cont_n(array) not in cont_n:
            continue

        if valid(three0) and count_three(array, 0) not in three0:
            continue
        if valid(three1) and count_three(array, 1) not in three1:
            continue
        if valid(three2) and count_three(array, 2) not in three2:
            continue

        if valid(four0) and count_four(array, 0) not in four0:
            continue
        if valid(four1) and count_four(array, 1) not in four1:
            continue
        if valid(four2) and count_four(array, 2) not in four2:
            continue
        if valid(four3) and count_four(array, 3) not in four3:
            continue

        if valid(range0) and count_range(array, 0) not in range0:
            continue
        if valid(range1) and count_range(array, 1) not in range1:
            continue
        if valid(range2) and count_range(array, 2) not in range2:
            continue
        if valid(last_win) and valid(last_nums) and \
           count_last(array, last_win) not in last_nums:
            continue

        if valid(first_odd):
            odd = array[0] % 2
            if first_odd and not odd:
                continue
            if not first_odd and odd:
                continue
        if valid(last_odd):
            odd = array[-1] % 2
            if last_odd and not odd:
                continue
            if not last_odd and odd:
                continue

        sum_n = count_sum(array)
        if valid(sum_low) and sum_n < sum_low:
            continue
        if valid(sum_high) and sum_n > sum_high:
            continue

        output_set.append(array)

    return output_set


class DBallFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.__set_properties()
        self.__create_objects()
        self.__do_layout()
        self.__do_setfont()

        self.result = []
        self.result_str = ""

    def __do_setfont(self):
        if g_os_windows:
            for item in self.items_all:
                item.SetFont(self.font)
            self.text_out.SetFont(self.font_small)

    def __create_objects(self):
        # Including bindings of the objects (mostly, buttons)
        if g_os_windows:
            self.font = wx.Font(wx.FontInfo(g_fontsize).Bold())
            self.font_small = wx.Font(wx.FontInfo(g_fontsize - 2).Bold())

        self.text_out = wx.TextCtrl(self, wx.ID_ANY, "", size=g_output_size,
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.last_win = wx.TextCtrl(self, wx.ID_ANY, "", size=g_lastwin_size)
        self.danma = wx.TextCtrl(self, wx.ID_ANY, "", size=g_lastwin_size)
        self.items_all = [self.text_out, self.last_win]

        self.buttons = []
        self.button_changelog = wx.Button(self, wx.ID_ANY, "更新日志")
        self.buttons.append(self.button_changelog)
        self.button_print = wx.Button(self, wx.ID_ANY, "输出结果")
        self.buttons.append(self.button_print)
        self.button_reset = wx.Button(self, wx.ID_ANY, "重置参数")
        self.buttons.append(self.button_reset)
        self.button_gen = wx.Button(self, wx.ID_ANY, "生成结果")
        self.buttons.append(self.button_gen)
        self.button_quit = wx.Button(self, wx.ID_ANY, "退出")
        self.buttons.append(self.button_quit)
        self.items_all += self.buttons

        # self.sum_low = wx.TextCtrl(self, wx.ID_ANY, "")
        # self.sum_high = wx.TextCtrl(self, wx.ID_ANY, "")
        self.first_odd = wx.Choice(self, wx.ID_ANY,
                                   choices=["任意", "奇数", "偶数"])
        self.last_odd = wx.Choice(self, wx.ID_ANY,
                                  choices=["任意", "奇数", "偶数"])
        # self.items_all += [self.sum_low, self.sum_high]
        # self.items_all += [self.first_odd, self.last_odd]

        self.checkboxes = []

        self.numbers = []
        #self.danma = []
        for i in range(1, 34):
            box = wx.CheckBox(self, wx.ID_ANY, "%02d" % i)
            self.numbers.append(box)
            #box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            #self.danma.append(box)
        self.checkboxes += self.numbers
        #self.checkboxes += self.danma

        if g_debug:
            for i in range(1, 10):
                self.numbers[i-1].SetValue(True)

        self.primes = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" %
                              (i, g_elements-i))
            self.primes.append(box)
        self.checkboxes += self.primes

        self.odds = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" %
                              (i, g_elements-i))
            self.odds.append(box)
        self.checkboxes += self.odds

        self.bigs = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" % (i, g_elements-i))
            self.bigs.append(box)
        self.checkboxes += self.bigs

        # self.acs = []
        # for i in range(1, 11):
        #     box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
        #     self.acs.append(box)
        # self.checkboxes += self.acs

        self.diff_tails = []
        for i in range(3, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.diff_tails.append(box)
        self.checkboxes += self.diff_tails

        self.crosses = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.crosses.append(box)
        self.checkboxes += self.crosses

        self.outters = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.outters.append(box)
        self.checkboxes += self.outters

        # divide 3
        self.three0 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.three0.append(box)
        self.checkboxes += self.three0
        self.three1 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.three1.append(box)
        self.checkboxes += self.three1
        self.three2 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.three2.append(box)
        self.checkboxes += self.three2

        # divide 4
        self.four0 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.four0.append(box)
        self.checkboxes += self.four0
        self.four1 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.four1.append(box)
        self.checkboxes += self.four1
        self.four2 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.four2.append(box)
        self.checkboxes += self.four2
        self.four3 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.four3.append(box)
        self.checkboxes += self.four3

        self.range0 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.range0.append(box)
        self.checkboxes += self.range0
        self.range1 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.range1.append(box)
        self.checkboxes += self.range1
        self.range2 = []
        for i in range(0, g_elements + 1):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.range2.append(box)
        self.checkboxes += self.range2

        self.conts = []
        for i in range(0, g_elements):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.conts.append(box)
        self.checkboxes += self.conts

        self.last_nums = []
        for i in range(0, 5):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.last_nums.append(box)
        self.checkboxes += self.last_nums

        self.items_all += self.checkboxes

        self.Bind(wx.EVT_BUTTON, self.do_generate, self.button_gen)
        self.Bind(wx.EVT_BUTTON, self.do_reset, self.button_reset)
        self.Bind(wx.EVT_BUTTON, self.do_quit, self.button_quit)
        self.Bind(wx.EVT_BUTTON, self.do_changelog, self.button_changelog)
        self.Bind(wx.EVT_BUTTON, self.do_print, self.button_print)

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
        for box in self.checkboxes:
            box.SetValue(False)
        # self.sum_low.SetValue("")
        # self.sum_high.SetValue("")
        self.first_odd.SetSelection(-1)
        self.last_odd.SetSelection(-1)
        self.last_win.SetValue("")
        self.out("所有参数已重置！")

    def __set_properties(self):
        if g_size:
            self.SetSize(g_size)
        # self.SetBackgroundColour(wx.Colour(94, 95, 95))

    def new_static(self, value):
        static = wx.StaticText(self, wx.ID_ANY, value)
        self.items_all.append(static)
        return static

    def __do_layout(self):
        # Most outter sizer
        sizer_all = wx.FlexGridSizer(1, 2, 5, 5)

        # 1st level
        sizer_conds = wx.FlexGridSizer(19, 2, 5, 5)
        sizer_right_all = wx.FlexGridSizer(2, 1, 5, 5)
        sizer_all.Add(sizer_conds, border=g_border, flag=g_flag)
        sizer_all.Add(sizer_right_all, border=g_border, flag=g_flag)

        # 2nd level
        sizer_conds_2 = wx.FlexGridSizer(12, 2, 5, 5)
        sizer_control = wx.FlexGridSizer(3, 1, 5, 5)
        sizer_right_all.Add(sizer_conds_2, border=g_border, flag=g_flag)
        sizer_right_all.Add(sizer_control, border=g_border, flag=g_flag)

        # Control REGION
        sizer_control.Add(self.text_out, border=g_border, flag=g_flag)
        sizer_buttons1 = wx.GridSizer(1, 3, 5, 5)
        sizer_buttons2 = wx.GridSizer(1, 2, 5, 5)
        for button in self.buttons[0:3]:
            sizer_buttons1.Add(button, flag=g_flag, border=g_border)
        for button in self.buttons[3:5]:
            sizer_buttons2.Add(button, flag=g_flag, border=g_border)
        sizer_control.Add(sizer_buttons1, border=g_border, flag=g_flag)
        sizer_control.Add(sizer_buttons2, border=g_border, flag=g_flag)

        # Conditions REGION
        sizer_numbers_in = wx.GridSizer(6, 6, g_border2, g_border2)
        for num in self.numbers:
            sizer_numbers_in.Add(num, border=0, flag=g_flag)

        sizer_primes = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for prime in self.primes:
            sizer_primes.Add(prime, border=0, flag=g_flag)
        sizer_odds = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for odd in self.odds:
            sizer_odds.Add(odd, border=0, flag=g_flag)
        sizer_bigs = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for big in self.bigs:
            sizer_bigs.Add(big, border=0, flag=g_flag)
        sizer_acs = wx.GridSizer(2, 5, g_border2, g_border2)
        # for ac in self.acs:
        #     sizer_acs.Add(ac, border=0, flag=g_flag)
        sizer_diff_tails = wx.GridSizer(1, 15, g_border2, g_border2)
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        for tail in self.diff_tails:
            sizer_diff_tails.Add(tail, border=0, flag=g_flag)
        sizer_crosses = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for cross in self.crosses:
            sizer_crosses.Add(cross, border=0, flag=g_flag)
        sizer_outters = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for outter in self.outters:
            sizer_outters.Add(outter, border=0, flag=g_flag)
        sizer_bigs = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for big in self.bigs:
            sizer_bigs.Add(big, border=0, flag=g_flag)
        # sizer_sum = wx.FlexGridSizer(1, 4, g_border2, g_border2)
        # sizer_sum.Add(self.new_static("        从"), border=0)
        # sizer_sum.Add(self.sum_low, border=0)
        # sizer_sum.Add(self.new_static("到"), border=0)
        # sizer_sum.Add(self.sum_high, border=0)

        sizer_three0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.three0:
            sizer_three0.Add(item, border=0, flag=g_flag)
        sizer_three1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.three1:
            sizer_three1.Add(item, border=0, flag=g_flag)
        sizer_three2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.three2:
            sizer_three2.Add(item, border=0, flag=g_flag)

        sizer_four0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.four0:
            sizer_four0.Add(item, border=0, flag=g_flag)
        sizer_four1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.four1:
            sizer_four1.Add(item, border=0, flag=g_flag)
        sizer_four2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.four2:
            sizer_four2.Add(item, border=0, flag=g_flag)
        sizer_four3 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.four3:
            sizer_four3.Add(item, border=0, flag=g_flag)

        sizer_range0 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.range0:
            sizer_range0.Add(item, border=0, flag=g_flag)
        sizer_range1 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.range1:
            sizer_range1.Add(item, border=0, flag=g_flag)
        sizer_range2 = wx.GridSizer(1, g_elements + 1, g_border2, g_border2)
        for item in self.range2:
            sizer_range2.Add(item, border=0, flag=g_flag)

        sizer_conts = wx.GridSizer(1, g_elements, g_border2, g_border2)
        for cont in self.conts:
            sizer_conts.Add(cont, border=0, flag=g_flag)

        sizer_last_win = wx.FlexGridSizer(1, 2, g_border2, g_border2)
        sizer_last_win.Add(self.last_win, border=0, flag=g_flag)
        sizer_last_win.Add(self.new_static("(例:01 02 03 04 05 06)"))
        sizer_last_nums = wx.GridSizer(1, 5, 3, 3)
        for item in self.last_nums:
            sizer_last_nums.Add(item, border=0, flag=g_flag)

        #sizer_danma_in = wx.GridSizer(6, 6, 3, 3)
        #for num in self.danma:
        #    sizer_danma_in.Add(num, border=0, flag=g_flag)

        sizer_danma_in = wx.FlexGridSizer(1, 2, 3, 3)
        sizer_danma_in.Add(self.danma, border=0, flag=g_flag)
        sizer_danma_in.Add(self.new_static("(例:01 02 03)"))

        sizer_conds.Add(self.new_static("数字选择："))
        sizer_conds.Add(sizer_numbers_in, border=0, flag=g_flag)
        sizer_conds_2.Add(self.new_static("胆码选择："))
        sizer_conds_2.Add(sizer_danma_in, border=0, flag=g_flag)
        sizer_conds.Add(self.new_static("质合比："))
        sizer_conds.Add(sizer_primes, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("大小比："))
        sizer_conds.Add(sizer_bigs, border=g_border, flag=g_flag)
        # sizer_conds.Add(self.new_static("AC值："))
        # sizer_conds.Add(sizer_acs, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("对角线："))
        sizer_conds.Add(sizer_crosses, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("外围个数："))
        sizer_conds.Add(sizer_outters, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除3余0："))
        sizer_conds.Add(sizer_three0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除3余1："))
        sizer_conds.Add(sizer_three1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除3余2："))
        sizer_conds.Add(sizer_three2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余0："))
        sizer_conds.Add(sizer_four0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余1："))
        sizer_conds.Add(sizer_four1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余2："))
        sizer_conds.Add(sizer_four2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("除4余3："))
        sizer_conds.Add(sizer_four3, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第一区间："))
        sizer_conds.Add(sizer_range0, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第二区间："))
        sizer_conds.Add(sizer_range1, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("第三区间："))
        sizer_conds.Add(sizer_range2, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("连号个数："))
        sizer_conds.Add(sizer_conts, border=g_border, flag=g_flag)

        sizer_conds_2.Add(self.new_static("首位奇偶："))
        #sizer_conds.Add(self.first_odd, border=g_border, flag=g_flag)
        #sizer_conds.Add(self.new_static("末位奇偶："))
        #sizer_conds.Add(self.last_odd, border=g_border, flag=g_flag)
        sizer_shoumojiou = wx.FlexGridSizer(1, 4, 0, 0)
        sizer_shoumojiou.Add(self.new_static("     "), border=0, flag=g_flag)
        sizer_shoumojiou.Add(self.first_odd, border=0, flag=g_flag)
        sizer_shoumojiou.Add(self.new_static("    末位奇偶：    "), border=0, flag=g_flag)
        sizer_shoumojiou.Add(self.last_odd, border=0, flag=g_flag)                             
        sizer_conds_2.Add(sizer_shoumojiou, border=0, flag=g_flag)

        sizer_conds.Add(self.new_static("不同尾数："))
        sizer_conds.Add(sizer_diff_tails, border=g_border, flag=g_flag)
        sizer_conds.Add(self.new_static("奇偶比："))
        sizer_conds.Add(sizer_odds, border=g_border, flag=g_flag)

        # sizer_conds_2.Add(self.new_static("和值范围："))
        # sizer_conds_2.Add(sizer_sum, border=g_border, flag=g_flag)
        sizer_conds_2.Add(self.new_static("上期结果："))
        sizer_conds_2.Add(sizer_last_win, border=g_border, flag=g_flag)
        sizer_conds_2.Add(self.new_static("上期重复："))
        sizer_conds_2.Add(sizer_last_nums, border=g_border, flag=g_flag)

        self.SetSizer(sizer_all)
        self.Layout()

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

        # try:
        #     s = self.sum_low.GetValue()
        #     if s == "":
        #         sum_low = -1
        #     else:
        #         sum_low = int(s)
        # except:
        #     self.out("错误：和值最小值输入有误")
        #     return
        # try:
        #     s = self.sum_high.GetValue()
        #     if s == "":
        #         sum_high = -1
        #     else:
        #         sum_high = int(s)
        # except:
        #     self.out("错误：和值最大值输入有误")
        #     return
        # if sum_low != -1 and sum_high != -1 and sum_low > sum_high:
        #     self.out("错误：和值最小值大于最大值，请重新输入")
        #     return

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
            "range0": range0,
            "range1": range1,
            "range2": range2,
            "last_win": last_win,
            "last_nums": last_nums,
        }
        self.result = dball_calc(params)
        self.do_show_result(self.result)

    def do_show_result(self, result):
        full_line = "-----------------------------------------------------------------------"
        self.out("缩水结果：\n%s" % full_line)
        if not result:
            self.result_str = ""
            self.out("未找到合适的结果，请修改缩水范围后重试。")
        else:
            start = 1
            result_str = "" 
            for entry in result:
                str_res = " ".join(map(lambda x: "%02d" % x, entry))
                result_str += "[%03s] %s" % (start, str_res)
                if start % 3:
                    result_str += " "
                else:
                    result_str += "\n"
                if start % 15 == 0:
                    result_str += full_line + "\n"
                start += 1
            self.result_str = result_str
            self.out(result_str)

    def do_quit(self, event):
        print("Quitting...")
        self.Close()

class MyMenuBar(wx.MenuBar):
    def __init__(self, *args, **kwds):
        wx.MenuBar.__init__(self, *args, **kwds)
        wxglade_tmp_menu = wx.Menu()
        self.Append(wxglade_tmp_menu, "&File")
        wxglade_tmp_menu = wx.Menu()
        self.Append(wxglade_tmp_menu, "&About")

class MyApp(wx.App):
    def OnInit(self):
        frame_main = DBallFrame(None,
                                wx.ID_ANY,
                                title=g_title,
                                style=g_style)
        self.SetTopWindow(frame_main)
        frame_main.Show()
        return True

if __name__ == "__main__":
    double_ball = MyApp(0)
    double_ball.MainLoop()
