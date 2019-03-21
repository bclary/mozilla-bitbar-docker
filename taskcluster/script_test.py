import pytest

import script

def test_find_command_in_args_normal():
  test_argv = ['111', '222', '333', '   --  ', 'haha', 'yay']
  assert script.find_command_in_args(test_argv) == ['haha', 'yay']

def test_find_command_in_args_raises():
  test_argv = ['111', '222', '333', 'haha', 'yay']
  with pytest.raises(Exception):
    script.find_command_in_args(test_argv)
