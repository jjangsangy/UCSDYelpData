# -*- coding: utf-8 -*-
import operator
import argparse
import os

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from .analysis import *

def command_line():

    args = ArgumentParser(
        prog='dict2dict',
        description=' '.join([
            'Use the power of Python dicts to convert seamlessly between',
            'multiple data interchange formats',
        ]),
        formatter_class=ArgumentDefaultsHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )
    args.add_argument(
        'file',
        help='Specify a dict file with proper serialization format',
    )
    args.add_argument(
        '--factory',
        help='Specify Output Format',
        choices=['csv', 'DataFrame', 'dict', 'excel', 'html', 'strata', 'latex', 'hdf', 'json', 'clipboard'],
        const='csv',
        default='csv',
        nargs='?',
        type=str,
    )
    args.add_argument(
        '--head',
        const=10,
        default=None,
        nargs='?',
        help='get only n head',
        type=int,
    )
    args.add_argument(
        '--dry_run',
        action='store_true',
        help='Like a desert',
    )

    return args.parse_args()


def main():
    args = command_line()

    index = 'user_id' if 'user' in args.file.lower() else 'business_id'

    directory = os.path.dirname(args.file) if os.path.dirname(args.file) else '.'

    print('Creating %s file in %s' % (args.factory, directory))
    df = to_df(args.file, index)

    if args.head:
        head = operator.methodcaller('head', args.head)
        df = head(df)

    if args.factory in ['csv', 'dict'] and not hasattr(args, 'dry_run'):

        original = args.file
        filename = original.replace(
            original.rpartition('.')[-1], args.factory
        )

        factory = operator.methodcaller(
            'to_'+args.factory,
            filename,
            chunksize=1028,
            encoding='utf-8',
        )
        factory(df)

    print(df.head())

if __name__ == '__main__':
    main()
