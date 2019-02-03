#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import wx
import math
from itertools import combinations, permutations
from datetime import datetime

g_debug = False
g_prime_list = [1,2,3,5,7,11,13,17,19,23,29,31]
g_cross_list = [1,6,8,11,15,16,21,22,26,29,31]
g_outter_list = [1,2,3,4,5,6,7,12,13,18,19,24,25,30,31,32,33]
g_size = (450, 630)
g_border = 3

if g_size:
    g_style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
else:
    g_style = wx.DEFAULT_FRAME_STYLE

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

# example:
# params = {
#     "num_list": [1,2,3,4,5,16,17,18,19,20,21,22,23],
#     "prime_n": [1,3,5],
#     "odd_n": [1,2,3],
#     "big_n": [1,2,3],
#     "sum_low": 30,
#     "sum_high": 50,
#     "ac_val": [2,3,4,5,6,7,8],
#     "diff_tail_n": -1,
#     "first_odd": 1,
#     "last_odd": 1,
#     "cross_n": -1,
#     "outter_n": -1,
#     "cont_n": 2,
# }
def dball_calc(params):
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

    input_set = combinations(num_list, 6)
    output_set = []

    for array in input_set:
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

    def __create_objects(self):
        # Including bindings of the objects (mostly, buttons)
        self.text_out = wx.TextCtrl(self, wx.ID_ANY, "",
                                    size=(-1, 100),
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.button_gen = wx.Button(self, wx.ID_ANY, "生成结果")
        self.button_reset = wx.Button(self, wx.ID_ANY, "重置参数")
        self.button_quit = wx.Button(self, wx.ID_ANY, "退出")
        self.sum_low = wx.TextCtrl(self, wx.ID_ANY, "")
        self.sum_high = wx.TextCtrl(self, wx.ID_ANY, "")
        self.first_odd = wx.Choice(self, wx.ID_ANY,
                                   choices=["任意", "奇数", "偶数"])
        self.last_odd = wx.Choice(self, wx.ID_ANY,
                                  choices=["任意", "奇数", "偶数"])

        self.checkboxes = []
        self.numbers = []
        for i in range(1, 34):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.numbers.append(box)
            self.checkboxes.append(box)
        self.primes = []
        for i in range(0, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" % (i, 6-i))
            self.primes.append(box)
            self.checkboxes.append(box)
        self.odds = []
        for i in range(0, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" % (i, 6-i))
            self.odds.append(box)
            self.checkboxes.append(box)
        self.bigs = []
        for i in range(0, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s:%s" % (i, 6-i))
            self.bigs.append(box)
            self.checkboxes.append(box)
        self.acs = []
        for i in range(1, 11):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.acs.append(box)
            self.checkboxes.append(box)
        self.diff_tails = []
        for i in range(3, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.diff_tails.append(box)
            self.checkboxes.append(box)
        self.crosses = []
        for i in range(0, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.crosses.append(box)
            self.checkboxes.append(box)
        self.outters = []
        for i in range(0, 7):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.outters.append(box)
            self.checkboxes.append(box)
        self.conts = []
        for i in range(0, 6):
            box = wx.CheckBox(self, wx.ID_ANY, "%s" % i)
            self.conts.append(box)
            self.checkboxes.append(box)

        self.Bind(wx.EVT_BUTTON, self.do_generate, self.button_gen)
        self.Bind(wx.EVT_BUTTON, self.do_reset, self.button_reset)
        self.Bind(wx.EVT_BUTTON, self.do_quit, self.button_quit)

    def do_reset(self, event):
        self.clear()
        for box in self.checkboxes:
            box.SetValue(False)
        self.sum_low.SetValue("")
        self.sum_high.SetValue("")
        self.first_odd.SetSelection(-1)
        self.last_odd.SetSelection(-1)
        self.out("所有参数已重置！")

    def __set_properties(self):
        if g_size:
            self.SetSize(g_size)
        # self.SetBackgroundColour(wx.Colour(94, 95, 95))

    def __do_layout(self):
        sizer_all = wx.FlexGridSizer(2, 1, 5, 5)
        sizer_buttons = wx.GridSizer(1, 3, 5, 5)
        sizer_conds = wx.FlexGridSizer(15, 2, 10, 10)

        sizer_numbers = wx.GridSizer(6, 6, 3, 3)
        for num in self.numbers:
            sizer_numbers.Add(num, proportion=1, border=0,
                              flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_primes = wx.GridSizer(1, 7, 3, 3)
        for prime in self.primes:
            sizer_primes.Add(prime, proportion=1, border=0,
                             flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_odds = wx.GridSizer(1, 7, 3, 3)
        for odd in self.odds:
            sizer_odds.Add(odd, proportion=1, border=0,
                           flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_bigs = wx.GridSizer(1, 7, 3, 3)
        for big in self.bigs:
            sizer_bigs.Add(big, proportion=1, border=0,
                           flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_acs = wx.GridSizer(1, 10, 3, 3)
        for ac in self.acs:
            sizer_acs.Add(ac, proportion=1, border=0,
                          flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_diff_tails = wx.GridSizer(1, 10, 3, 3)
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        sizer_diff_tails.Add(wx.StaticText(self, wx.ID_ANY, ""))
        for tail in self.diff_tails:
            sizer_diff_tails.Add(tail, proportion=1, border=0,
                                 flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_crosses = wx.GridSizer(1, 7, 3, 3)
        for cross in self.crosses:
            sizer_crosses.Add(cross, proportion=1, border=0,
                              flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_outters = wx.GridSizer(1, 7, 3, 3)
        for outter in self.outters:
            sizer_outters.Add(outter, proportion=1, border=0,
                              flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_bigs = wx.GridSizer(1, 7, 3, 3)
        for big in self.bigs:
            sizer_bigs.Add(big, proportion=1, border=0,
                           flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_sum = wx.GridSizer(1, 6, 3, 3)
        sizer_sum.Add(wx.StaticText(self, wx.ID_ANY, "从"),
                      proportion=1, border=0,
                      flag=wx.ALIGN_CENTER)
        sizer_sum.Add(self.sum_low, proportion=1, border=0)
        sizer_sum.Add(wx.StaticText(self, wx.ID_ANY, ""),
                      proportion=1, border=0,
                      flag=wx.ALIGN_CENTER)
        sizer_sum.Add(wx.StaticText(self, wx.ID_ANY, "到"),
                      proportion=1, border=0,
                      flag=wx.ALIGN_CENTER)
        sizer_sum.Add(self.sum_high, proportion=1, border=0)

        sizer_all.Add(sizer_conds, proportion=1, border=g_border,
                      flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_all.Add(sizer_buttons, proportion=1, border=g_border,
                      flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND|
                      wx.ALIGN_BOTTOM)
        sizer_conts = wx.GridSizer(1, 6, 3, 3)
        for cont in self.conts:
            sizer_conts.Add(cont, proportion=1, border=0,
                           flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND)

        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "选择数字："))
        sizer_conds.Add(sizer_numbers, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "质和比："))
        sizer_conds.Add(sizer_primes, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "奇偶比："))
        sizer_conds.Add(sizer_odds, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "大小比："))
        sizer_conds.Add(sizer_bigs, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "AC值："))
        sizer_conds.Add(sizer_acs, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "不同尾数个数："))
        sizer_conds.Add(sizer_diff_tails, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "对角线个数："))
        sizer_conds.Add(sizer_crosses, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "外围个数："))
        sizer_conds.Add(sizer_outters, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "首位奇偶："))
        sizer_conds.Add(self.first_odd, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "末位奇偶："))
        sizer_conds.Add(self.last_odd, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "和值范围："))
        sizer_conds.Add(sizer_sum, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)
        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "连号个数："))
        sizer_conds.Add(sizer_conts, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)

        sizer_conds.Add(wx.StaticText(self, wx.ID_ANY, "输出结果："))
        sizer_conds.Add(self.text_out, proportion=1, border=g_border,
                        flag=wx.LEFT|wx.RIGHT|wx.EXPAND)

        for button in [self.button_gen, self.button_reset, self.button_quit]:
            sizer_buttons.Add(button, proportion=1,
                              flag=wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.ALIGN_RIGHT,
                              border=g_border)

        self.SetSizer(sizer_all)
        self.Layout()

    def out(self, line):
        self.text_out.AppendText(unicode(line + "\n", "utf-8"))

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

    def get_choice(self, item):
        value = item.GetSelection()
        if value == 0 or value == -1:
            return -1
        elif value == 1:
            return 1
        elif value == 2:
            return 0
        raise Exception("Unknown value: %s" % value)

    def do_generate(self, event):
        self.clear()

        #
        # Get the values, report if there's error when parsing
        #
        nums = self.get_nums()
        if len(nums) < 6:
            self.out("错误：清选择至少6个备选数字")
            return
        primes = self.get_primes()
        odds = self.get_odds()
        bigs = self.get_bigs()
        acs = self.get_acs()
        diff_tails = self.get_diff_tails()
        crosses = self.get_crosses()
        outters = self.get_outters()
        first_odd = self.get_choice(self.first_odd)
        last_odd = self.get_choice(self.last_odd)
        conts = self.get_conts()

        try:
            s = self.sum_low.GetValue()
            if s == "":
                sum_low = -1
            else:
                sum_low = int(s)
        except:
            self.out("错误：和值最小值输入有误")
            return
        try:
            s = self.sum_high.GetValue()
            if s == "":
                sum_high = -1
            else:
                sum_high = int(s)
        except:
            self.out("错误：和值最大值输入有误")
            return

        if sum_low != -1 and sum_high != -1 and sum_low > sum_high:
            self.out("错误：和值最小值大于最大值，请重新输入")
            return

        if g_debug:
            self.out("==缩水条件==")
            self.out("所选数字: %s" % nums)
            self.out("质数个数: %s" % (primes if primes else "<任意>"))
            self.out("奇数个数: %s" % (odds if odds else "<任意>"))
            self.out("大数个数: %s" % (bigs if bigs else "<任意>"))
            self.out("可选AC数值: %s" % (acs if acs else "<任意>"))
            self.out("不同尾数个数: %s" % (diff_tails if diff_tails else "<任意>"))
            self.out("对角线个数: %s" % (crosses if crosses else "<任意>"))
            self.out("外围个数: %s" % (outters if outters else "<任意>"))
            self.out("首位奇数: %s" % (first_odd if first_odd != -1 else "<任意>"))
            self.out("末位奇数: %s" % (last_odd if last_odd != -1 else "<任意>"))
            self.out("和值范围：%s - %s" %
                     (sum_low if sum_low is not -1 else "<任意>",
                      sum_high if sum_high is not -1 else "<任意>"))
            self.out("连号个数: %s" % (conts if conts else "<任意>"))
        params = {
            "num_list": nums,
            "prime_n": primes,
            "odd_n": odds,
            "big_n": bigs,
            "sum_low": sum_low,
            "sum_high": sum_high,
            "ac_val": acs,
            "diff_tail_n": diff_tails,
            "first_odd": first_odd,
            "last_odd": last_odd,
            "cross_n": crosses,
            "outter_n": outters,
            "cont_n": conts,
        }
        result = dball_calc(params)
        self.out("==缩水结果==")
        if not result:
            self.out("未找到合适的结果，请修改缩水范围后重试。")
        else:
            start = 1
            for entry in result:
                self.out("%03d: %s" % (start, entry))
                start += 1

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
                                title="双色球缩水工具",
                                style=g_style)
        self.SetTopWindow(frame_main)
        frame_main.Show()
        return True

if __name__ == "__main__":
    double_ball = MyApp(0)
    double_ball.MainLoop()
