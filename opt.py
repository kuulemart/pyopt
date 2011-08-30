import sys
import string
import fileinput
import collections


Transaction = collections.namedtuple('Transaction', 'debtors,creditors,amount')


class Solver:

    def _update_saldo(self, saldo, transaction):
        def _update(lst, i = 1):
            amt = transaction.amount / len(lst)
            for item in lst:
                saldo[item] = saldo.get(item, 0) + amt*i
        _update(transaction.debtors, -1)
        _update(transaction.creditors)

    def __call__(self, transactions):
        saldo  = {}

        for transaction in transactions:
            self._update_saldo(saldo, transaction)

        saldo = [item for item in saldo.items() if item[1]]
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


class Transform:

    def read(self, lines):
        for line in lines:
            if line:
                actors, amount = line.split(':')
                amount = float(amount)
                debtors, x, creditors = actors.partition('>')
                if not x:
                    creditors, x, debtors = actors.partition('<')
                yield Transaction(map(string.strip, debtors.split(',')),
                                  map(string.strip, creditors.split(',')),
                                  amount)

    def dump(self, transactions):
        def _dump_t(t):
            return '%s > %s : %s' %\
                (','.join(t.debtors),
                 ','.join(t.creditors),
                 t.amount)

        for transaction in transactions:
            print _dump_t(transaction)


class Opt:
    def __init__(self, transform, solver):
        self.transform = transform
        self.solver = solver

    def run(self, data):
        txs = self.transform.read(data)
        solved_txs = self.solver(txs)
        self.transform.dump(solved_txs)


if __name__ == '__main__':
    opt = Opt(Transform(), Solver())
    opt.run(fileinput.input(sys.argv[1:]))
