from typing import Any


class NumberHelper:
    @staticmethod
    def getFloatOrIntOrNone( value:Any ) -> float or int or None:
        """
        checks if a given value is float or int or can be converted to float or int
        and returns the appropriate value or None if value can't be converted
        :param value:
        :return:
        """
        if not value: return None
        if type(value) in (float, int): return value
        if type(value) != str: return None
        plus, minus, pkt = 0, 0, 0
        is_float = False
        s = ""
        for c in value:
            if c == '+':
                if len( s ) > 0: return None
                plus += 1
            elif c == '-':
                if len( s ) > 0: return None
                minus += 1
            elif c == '.':
                is_float = True
                pkt += 1
            else:
                if not c.isdigit(): return None
            s += c
        if plus > 1 or minus > 1 or pkt > 1: return None
        if is_float: return float( value )
        else: return int( value )

def test():
    r = NumberHelper.getFloatOrIntOrNone( "-p.0" )
    print( "type(r): ", type(r), "  value: ", r )