#!/usr/bin/env python3

import sys
import string
import fileinput
import collections
import decimal
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('opt')

# transaction
Tx = collections.namedtuple('Tx', 'debtors,creditors,amount')


class PluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)

    def get(cls, name, *p, **kw):
        for plugin in cls.plugins:
            if plugin.name == name:
                return plugin(*p, **kw)
        raise Exception('Unknown plugin %s' % name)


class Solver(metaclass=PluginMount):
    pass

class Transformer(metaclass=PluginMount):
    pass

# ... existing code ...

class SimpleSolver(Solver):
    """Simplifies transactions"""

    name = 'simple'

    def _get_saldo(self, txs):
        saldo = {}
        def _update(names, amount):
            _amt = amount / len(names)
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


class DirectedTransformer(Transformer):
    """Transform data to and from textual representation"""

    name = 'directed'

    def __init__(self, sym_sep=',', sym_debt='>', sym_cred='<', sym_amnt=':'):
        self.sym_sep = sym_sep
        self.sym_debt = sym_debt
        self.sym_cred = sym_cred
        self.sym_amnt = sym_amnt

    def _split(self, names):
        return list(map(str.strip, names.split(self.sym_sep)))

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
                except Exception as e:
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
            print(_dump_t(tx))


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
    transformer = Transformer.get('directed')
    solver = Solver.get('simple')
    dataiter = fileinput.input(sys.argv[1:])
    opt = Opt(transformer, solver)
    opt.run(dataiter)
