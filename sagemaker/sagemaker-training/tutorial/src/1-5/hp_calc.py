import os, argparse
parser = argparse.ArgumentParser()
parser.add_argument('--first-num', type=int)
parser.add_argument('--second-num', type=int)
parser.add_argument('--operator', type=str)
parser.add_argument('--model_dir', type=str)
args = parser.parse_args()
if args.operator == 'p':
    print(f'The answer is {args.first_num + args.second_num}')
elif args.operator == 'm':
    print(f'The answer is {args.first_num - args.second_num}')
exit()