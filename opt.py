import shlex

class Transaction:
    def __init__(self, debtors = None, creditors = None, amount = 0):
        self.debtors = debtors
        self.creditors = creditors
        self.amount = float(amount)

    def update_saldo(self, saldo):
        def _update(lst, i = 1):
            amt = self.amount / len(lst)
            for item in lst:
                saldo[item] = saldo.get(item, 0) + amt*i
        _update(self.debtors, -1)
        _update(self.creditors)



class Transactions:
    def __init__(self, transactions = None):
        self.transactions = transactions or []

    def add(self, transaction):
        self.transactions.append(transaction)

    def solve(self, solver):
        saldo = {}
        for transaction in self.transactions:
            transaction.update_saldo(saldo)

        return Transactions(list(solver(saldo)))


def solver(saldo):
    saldo = saldo.items()
    saldo.sort(key = lambda x:x[1])

    while saldo:
        debtor,debt = saldo.pop(0)
        debt = abs(debt)
        creditor,credit = saldo.pop()
        amount = credit
        if debt != credit:
            if debt < credit:
                amount = debt
                saldo.append((creditor, credit - debt))
            else:
                saldo.append((debtor, credit - debt))
            saldo.sort(key = lambda x:x[1])

        yield Transaction([debtor], [creditor], amount)


class Parser:
    def __init__(self):
        self.stack = []
        self.state = 0

    def got_comma(self):
        pass

    def got_gt(self):
        pass

    def got_lt(self):
        pass

    def got_colon(self):
        pass

    def got_nl(self):
        pass

    def __call__(self, data):
        lexer = shlex.shlex(data+'\n')
        lexer.whitespace = ' \t\r'

        st_map = {(0,','):(0,self.got_colon),
                  (0,'>'):(1,self.got_gt),
                  (0,'<'):(1,self.got_lt),
                  (1,','):(1,self.got_comma),
                  (1,':'):(2,self.got_colon),
                  (2,'\n'):(0,self.got_nl)
                 }

        for token in lexer:
            key = (self.state, token)
            if key in st_map:
                state, func =  st_map[key]
                func()
                self.state = state
            else:
                self.stack.append(token)

        if self.state:
            raise Exception('Error parsing data')


def printer(transactions):
    def print_transaction(t):
        return '%s > %s : %s' %\
            (','.join(t.debtors),
             ','.join(t.creditors),
             t.amount)

    return '\n'.join(map(print_transaction,
                         transactions))


data = """
D>A:1
D>C:1
E>B:3
F>A:2
F>B:2
F>C:2
"""

t = Transactions()
t.add(Transaction(['D'],['A'],1))
t.add(Transaction(['D'],['C'],1))
t.add(Transaction(['E'],['B'],3))
t.add(Transaction(['F'],['A'],2))
t.add(Transaction(['F'],['B'],2))
t.add(Transaction(['F'],['C'],2))
print 'original:\n',printer(t)
tt = t.solve(solver)
print 'solved:\n',printer(tt) 
