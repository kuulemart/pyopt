#!/usr/bin/env python

import sys
import string
import fileinput
import collections
import decimal
import logging

logging.basicConfig(level = logging.INFO)
LOG = logging.getLogger()

# transaction
Tx = collections.namedtuple('Tx', 'debtors,creditors,amount')


class Solver:
    """Simplifies transactions"""
    def _get_saldo(self, txs):
        saldo = {}
        def _update(names, amount):
            _amt = amount / len(names)
            #_amt = _amt.quantize(decimal.Decimal('0.01'))
            for name in names:
                saldo[name] = saldo.get(name, 0) + _amt
        for tx in txs:
            _update(tx.debtors, -1*tx.amount)
            _update(tx.creditors, tx.amount)
        return [item for item in saldo.items() if item[1]]

    def solve(self, txs):
        saldo = self._get_saldo(txs) 
        saldo.sort(key = lambda x:x[1])

        while saldo:
            logging.debug('saldo: %s' % saldo)
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
            
            tx = Tx([debtor], [creditor], amount)
            logging.debug('tx: %s' % str(tx))

            yield tx


class Transformer:
    """Transform data to and from textual representation"""
    def __init__(self, sym_sep=',', sym_debt='>', sym_cred='<', sym_amnt=':'):
        self.sym_sep = sym_sep
        self.sym_debt = sym_debt
        self.sym_cred = sym_cred
        self.sym_amnt = sym_amnt

    def _split(self, names):
        return map(string.strip, names.split(self.sym_sep))

    def _money(self, amount):
        return str(amount.quantize(decimal.Decimal('0.01')))

    def read(self, iterator):
        for line in iterator:
            if line:
                try:
                    actors, x, amount = line.partition(self.sym_amnt)
                    if not x:
                        continue
                    debtors, x, creditors = actors.partition(self.sym_debt)
                    if not x:
                        creditors, x, debtors = actors.partition(self.sym_cred)
                    if not x:
                        continue
                    yield Tx(self._split(debtors),
                             self._split(creditors),
                             decimal.Decimal(amount))
                except Exception, e:
                    raise Exception('Exception %s in line: %s' % (e, line))

    def dump(self, txs):
        def _dump_t(tx):
            return '%s %s %s %s %s' %\
                (','.join(tx.debtors),
                self.sym_debt,
                 ','.join(tx.creditors),
                 self.sym_amnt,
                 self._money(tx.amount))

        for tx in txs:
            print _dump_t(tx)


class Opt:
    """Main optimizer class"""
    def __init__(self, transformer, solver):
        self.transformer = transformer
        self.solver = solver

    def run(self, data):
        txs = self.transformer.read(data)
        solved_txs = self.solver.solve(txs)
        self.transformer.dump(solved_txs)


if __name__ == '__main__':
    opt = Opt(Transformer(), Solver())
    opt.run(fileinput.input(sys.argv[1:]))
