#!/usr/bin/env python3

import unittest
from unittest.mock import MagicMock
import random
from io import StringIO
import json
import os

import shogi
import annotator.__main__ as annotator


class test_eval_absolute(unittest.TestCase):

    def test_white_unpadded(self):
        result = annotator.eval_absolute(10.01, True)
        self.assertEqual(result, 10.01)

    def test_white_padded(self):
        result = annotator.eval_absolute(10, True)
        self.assertEqual(result, 10.00)

    def test_black(self):
        result = annotator.eval_absolute(10.00, False)
        self.assertEqual(result, -10.00)


class test_eval_numeric(unittest.TestCase):

    def test_raises_runtimeerror(self):
        score = MagicMock()
        score.mate = None
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}
        self.assertRaises(RuntimeError, annotator.eval_numeric, info_handler)

    def test_dtm_positive(self):
        score = MagicMock()
        score.mate = 5
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}

        result = annotator.eval_numeric(info_handler)
        self.assertEqual(result, 9995)

    def test_dtm_negative(self):
        score = MagicMock()
        score.mate = -5
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}

        result = annotator.eval_numeric(info_handler)
        self.assertEqual(result, -9995)

    def test_cp_positive(self):
        score = MagicMock()
        score.mate = None
        score.cp = 5
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}

        result = annotator.eval_numeric(info_handler)
        self.assertEqual(result, 5)

    def test_cp_negative(self):
        score = MagicMock()
        score.mate = None
        score.cp = -5
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}

        result = annotator.eval_numeric(info_handler)
        self.assertEqual(result, -5)


class test_winning_chances(unittest.TestCase):

    def test_zero(self):
        score = 0
        result = round(annotator.winning_chances(score))
        self.assertEqual(result, 50)

    def test_one(self):
        score = 100
        result = round(annotator.winning_chances(score))
        self.assertEqual(result, 60)

    def test_four(self):
        score = 400
        result = round(annotator.winning_chances(score))
        self.assertEqual(result, 83)

    def test_negative_one(self):
        score = -100
        result = round(annotator.winning_chances(score))
        self.assertEqual(result, 40)

    def test_negative_four(self):
        score = -400
        result = round(annotator.winning_chances(score))
        self.assertEqual(result, 17)

    def test_raises_typeerror(self):
        score = 'a'
        self.assertRaises(TypeError, annotator.winning_chances, score)


class test_needs_annotation(unittest.TestCase):

    def test_high(self):
        judgment = {}
        judgment["besteval"] = 200
        judgment["playedeval"] = 100
        result = annotator.needs_annotation(judgment)
        self.assertTrue(result)

    def test_low(self):
        judgment = {}
        judgment["besteval"] = 5
        judgment["playedeval"] = 0
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_negative(self):
        judgment = {}
        judgment["besteval"] = 0
        judgment["playedeval"] = 100
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_zero(self):
        judgment = {}
        judgment["besteval"] = 0
        judgment["playedeval"] = 0
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_low_fraction(self):
        judgment = {}
        judgment["besteval"] = 5.333333
        judgment["playedeval"] = 0
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_high_fraction(self):
        judgment = {}
        judgment["besteval"] = 500.33333
        judgment["playedeval"] = 0
        result = annotator.needs_annotation(judgment)
        self.assertTrue(result)

    def test_small_error_big_advantage(self):
        judgment = {}
        judgment["besteval"] = 600
        judgment["playedeval"] = 500
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_small_error_big_disadvantage(self):
        judgment = {}
        judgment["besteval"] = -500
        judgment["playedeval"] = -600
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_big_error_huge_advantage(self):
        judgment = {}
        judgment["besteval"] = 9998
        judgment["playedeval"] = 1000
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_big_error_huge_disadvantage(self):
        judgment = {}
        judgment["besteval"] = -1000
        judgment["playedeval"] = -9998
        result = annotator.needs_annotation(judgment)
        self.assertFalse(result)

    def test_raises_typeerror(self):
        self.assertRaises(TypeError, annotator.needs_annotation, 'a')


class test_cpl(unittest.TestCase):

    def test_int(self):
        result = annotator.cpl(5)
        self.assertEqual(result, 5)

    def test_string(self):
        result = annotator.cpl('5')
        self.assertEqual(result, 5)

    def test_bigstring(self):
        result = annotator.cpl('1000')
        self.assertEqual(result, 1000)

    def test_negativestring(self):
        result = annotator.cpl('-2001')
        self.assertEqual(result, -2001)

    def test_max_cpl(self):
        result = annotator.cpl('5000')
        self.assertEqual(result, annotator.MAX_CPL)


class test_acpl(unittest.TestCase):

    def test_list(self):
        testlist = [1, 2, 3, 4, 5, 6]
        result = annotator.acpl(testlist)
        self.assertEqual(result, 3.5)


class test_eco_fen(unittest.TestCase):

    def test_board(self):
        board = shogi.Board('Q4R2/3kr3/1q3n1p/2p1p1p1/1p1bP1P1/1B1P3P/2PBK3/8 w - - 1 0')  # noqa E501
        result = annotator.eco_fen(board)
        self.assertEqual(result, 'Q4R2/3kr3/1q3n1p/2p1p1p1/1p1bP1P1/1B1P3P/2PBK3/8 w -')  # noqa E501


class test_get_total_budget(unittest.TestCase):

    def test_is_float(self):
        result = annotator.get_total_budget(random.random())
        self.assertIsInstance(result, float)

    def test_math(self):
        seed = random.random()
        result = annotator.get_total_budget(seed)
        self.assertEqual(result, seed * 60)

    def test_raises_valueerror(self):
        self.assertRaises(ValueError, annotator.get_total_budget, 'a')


class test_truncate_pv(unittest.TestCase):

    def test_long_mating_pv(self):
        """ A long pv that ends the game should not be truncated """

        board = shogi.Board('1Q3bk1/5p2/2p3p1/1p1bN2p/4n2P/8/r5PK/8 b - - 1 34')  # noqa E501
        line = [shogi.Move.from_usi('g8g7'), shogi.Move.from_usi('e5f7'),
                shogi.Move.from_usi('d5f7'), shogi.Move.from_usi('b8e5'),
                shogi.Move.from_usi('e4f6'), shogi.Move.from_usi('h2h3'),
                shogi.Move.from_usi('b5b4'), shogi.Move.from_usi('g2g4'),
                shogi.Move.from_usi('f8d6'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('h5g4'), shogi.Move.from_usi('h3g3'),
                shogi.Move.from_usi('f6e4'), shogi.Move.from_usi('g3f4'),
                shogi.Move.from_usi('e4d6'), shogi.Move.from_usi('f4e5'),
                shogi.Move.from_usi('b4b3'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('b3b2'), shogi.Move.from_usi('h4h5'),
                shogi.Move.from_usi('g6h5'), shogi.Move.from_usi('d6d7'),
                shogi.Move.from_usi('b2b1q'), shogi.Move.from_usi('d7c7'),
                shogi.Move.from_usi('b1b4'), shogi.Move.from_usi('c7c6'),
                shogi.Move.from_usi('a2c2'), shogi.Move.from_usi('c6d7'),
                shogi.Move.from_usi('b4b8'), shogi.Move.from_usi('d7e7'),
                shogi.Move.from_usi('b8c7')]
        result = annotator.truncate_pv(board, line)
        self.assertEqual(result, line)

    def test_long_non_mating_pv(self):
        """
        A long pv that does not end the game should be truncated to 10 moves
        """

        board = shogi.Board('1Q3bk1/5p2/2p3p1/1p1bN2p/4n2P/8/r5PK/8 b - - 1 34')  # noqa E501
        line = [shogi.Move.from_usi('g8g7'), shogi.Move.from_usi('e5f7'),
                shogi.Move.from_usi('d5f7'), shogi.Move.from_usi('b8e5'),
                shogi.Move.from_usi('e4f6'), shogi.Move.from_usi('h2h3'),
                shogi.Move.from_usi('b5b4'), shogi.Move.from_usi('g2g4'),
                shogi.Move.from_usi('f8d6'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('h5g4'), shogi.Move.from_usi('h3g3'),
                shogi.Move.from_usi('f6e4'), shogi.Move.from_usi('g3f4'),
                shogi.Move.from_usi('e4d6'), shogi.Move.from_usi('f4e5'),
                shogi.Move.from_usi('b4b3'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('b3b2'), shogi.Move.from_usi('h4h5'),
                shogi.Move.from_usi('g6h5'), shogi.Move.from_usi('d6d7'),
                shogi.Move.from_usi('b2b1q'), shogi.Move.from_usi('d7c7'),
                shogi.Move.from_usi('b1b4'), shogi.Move.from_usi('c7c6'),
                shogi.Move.from_usi('a2c2'), shogi.Move.from_usi('c6d7'),
                shogi.Move.from_usi('b4b8'), shogi.Move.from_usi('d7e7')]
        target = line[:annotator.SHORT_PV_LEN]
        result = annotator.truncate_pv(board, line)
        self.assertEqual(len(result), annotator.SHORT_PV_LEN)
        self.assertEqual(result, target)

    def test_raises_assertionerror(self):
        """ A line with an illegal move should raise an AssertionError """

        board = shogi.Board('1Q3bk1/5p2/2p3p1/1p1bN2p/4n2P/8/r5PK/8 b - - 1 34')  # noqa E501
        line = [shogi.Move.from_usi('g8g7'), shogi.Move.from_usi('e5f7'),
                shogi.Move.from_usi('d5f7'), shogi.Move.from_usi('b8e5'),
                shogi.Move.from_usi('e4f6'), shogi.Move.from_usi('h2h3'),
                shogi.Move.from_usi('b5b4'), shogi.Move.from_usi('g2g4'),
                shogi.Move.from_usi('f8d6'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('h5g4'), shogi.Move.from_usi('h3g3'),
                shogi.Move.from_usi('f6e4'), shogi.Move.from_usi('g3f4'),
                shogi.Move.from_usi('e4d6'), shogi.Move.from_usi('f4e5'),
                shogi.Move.from_usi('b4b3'), shogi.Move.from_usi('e5d6'),
                shogi.Move.from_usi('b3b2'), shogi.Move.from_usi('h4h5'),
                shogi.Move.from_usi('g6h5'), shogi.Move.from_usi('d6c8'),
                shogi.Move.from_usi('b2b1q'), shogi.Move.from_usi('d7c7'),
                shogi.Move.from_usi('b1b4'), shogi.Move.from_usi('c7c6'),
                shogi.Move.from_usi('a2c2'), shogi.Move.from_usi('c6d7'),
                shogi.Move.from_usi('b4b8'), shogi.Move.from_usi('d7e7'),
                shogi.Move.from_usi('b8c7')]
        self.assertRaises(AssertionError, annotator.truncate_pv, board, line)


class test_get_nags(unittest.TestCase):

    def test_zero(self):
        judgment = {'playedeval': 0, 'besteval': 0}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [])

    def test_negative(self):
        judgment = {'playedeval': 0, 'besteval': -10}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [])

    def test_float(self):
        judgment = {'playedeval': 0.001, 'besteval': -10.05}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [])

    def test_blunder(self):
        judgment = {'playedeval': 0, 'besteval': 350}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [shogi.pgn.NAG_BLUNDER])

    def test_mistake(self):
        judgment = {'playedeval': 0, 'besteval': 200}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [shogi.pgn.NAG_MISTAKE])

    def test_dubious(self):
        judgment = {'playedeval': 0, 'besteval': 100}
        result = annotator.get_nags(judgment)
        self.assertEqual(result, [shogi.pgn.NAG_DUBIOUS_MOVE])

    def test_typeerror(self):
        judgment = {'playedeval': 0, 'besteval': 'foo'}
        self.assertRaises(TypeError, annotator.get_nags, judgment)


class test_var_end_comment(unittest.TestCase):

    def test_stalemate(self):
        board = shogi.Board(fen='7k/8/6Q1/8/8/8/8/K7 b - - 0 1')
        judgment = {'bestcomment': "", 'depth': ""}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "Stalemate")

    def test_insufficient_material(self):
        board = shogi.Board(fen='7k/8/8/8/8/8/N7/K7 b - - 0 1')
        judgment = {'bestcomment': "", 'depth': ""}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "Insufficient material to mate")

    def test_fifty_move_rule(self):
        board = shogi.Board(fen='7k/8/8/8/8/1P6/N7/K7 b - - 100 150')
        judgment = {'bestcomment': "", 'depth': ""}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "Fifty move rule")

    def test_threefold_repetition(self):
        board = shogi.Board(fen='7k/8/8/8/8/1P6/N7/K7 b - - 0 1')
        moves = ["Kg8", "Nc1", "Kh8", "Na2", "Kg8", "Nc1", "Kh8", "Na2", "Kg8",
                 "Nc1", "Kh8", "Na2"]
        for move in moves:
            board.push_san(move)
        judgment = {'bestcomment': "", 'depth': ""}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "Three-fold repetition")

    def test_checkmate(self):
        board = shogi.Board(fen='8/8/8/8/8/1K6/8/1k1R4 b - - 0 1')
        judgment = {'bestcomment': "", 'depth': ""}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "")

    def test_other(self):
        board = shogi.Board(fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')  # noqa E501
        judgment = {'bestcomment': "foo", 'depth': "bar"}
        result = annotator.var_end_comment(board, judgment)
        self.assertEqual(result, "foo/bar")


class test_add_annotation(unittest.TestCase):
    pass


class test_classify_fen(unittest.TestCase):

    def test_eco_json(self):
        ecopath = os.path.join(
            os.path.dirname(__file__), '../annotator/eco/eco.json'
        )
        with open(ecopath, 'r') as ecofile:
            ecodata = json.load(ecofile)

            for row in ecodata:
                fen = "{} {}".format(row["f"], '- 0 1')
                shogi.Board(fen=fen)

                classification = annotator.classify_fen(row["f"], ecodata)

                assert classification["code"] == row["c"]
                assert classification["desc"] == row["n"]
                assert classification["path"] == row["m"]


class test_clean_game(unittest.TestCase):

    def test_commented_game(self):
        pgn_string = "{ Stockfish 8 64 POPCNT } 1. Nf3 { test comment } Nf6 2. g3 g6 { A05 King's Indian Attack: Symmetrical Defense } 3. Bg2 Bg7 4. O-O O-O 5. c4 d6 6. b3 e5 7. Bb2 c5 8. e3 Nc6 9. Nc3 Bf5 10. d4 e4 11. Ne1 Re8 12. Nc2 h5 13. Qd2 h4 14. Ba3 $6 { -1.13 } ( 14. h3 g5 15. g4 Bg6 16. Rad1 Qe7 17. Qe2 a6 18. Ba3 a5 { 0.19/25 } ) 14...  b6 $6 { -0.04 } ( 14... Nh7 15. Nd5 Ng5 16. Bb2 Rc8 17. Rac1 Ne7 18. Nf4 h3 19.  Bh1 { -1.11/24 } ) 15. Rfd1 $6 { -1.15 } ( 15. h3 d5 16. g4 Be6 17. cxd5 Nxd5 18. Nxe4 f5 19. gxf5 gxf5 { 0.00/26 } ) 15... Bg4 16. Rdc1 Qd7 17. b4 Qf5 18.  Bb2 Rad8 19. Nb5 Bf3 20. d5 Ne5 $6 { -1.66 } ( 20... Nxb4 21. Ne1 Bxg2 22.  Nxg2 Nd3 23. Nxh4 Qh3 24. Bxf6 Bxf6 25. f4 { -3.14/25 } ) 21. Bxe5 Rxe5 22.  Ne1 hxg3 23. fxg3 Bh6 24. Rab1 Kg7 $6 { -1.08 } ( 24... Qh5 25. Rb3 Rf5 26.  bxc5 dxc5 27. Rc2 Ng4 28. h3 Bxg2 29. Kxg2 { -2.48/24 } ) 25. Rb3 Qh5 26. h3 $6 { -3.08 } ( 26. bxc5 bxc5 27. Nxa7 Rh8 28. h4 Qg4 29. Nc6 Rh5 30. Qf2 Bd1 { -2.00/23 } ) 26... Nh7 $2 { -1.37 } ( 26... Rg5 27. Qf2 { -2.89/24 }) 27. g4 Bxg4 28. hxg4 Qxg4 29. Qd1 $4 { -5.69 } ( 29. Qb2 Ng5 30. Nxd6 Qg3 31. Nf5+ gxf5 32. Kf1 Nf3 33. Qf2 Nh2+ { -2.30/24 } ) 29... Qg3 30. Qe2 Ng5 31. Kh1 Rh8 32. Nxd6 Kg8 33. bxc5 Bf8+ 34. Kg1 Nh3+ 35. Kf1 Bxd6 36. cxd6 Rf5+ 37. Nf3 Rxf3+ 0-1"  # noqa E501
        pgn = StringIO(pgn_string)
        game = shogi.pgn.read_game(pgn)
        result = annotator.clean_game(game)
        node = result.end()
        while True:
            assert len(node.variations) <= 1
            assert node.comment is None
            assert node.nags == []
            if node == game.root():
                break
            node = node.parent


class test_game_length(unittest.TestCase):

    def test_commented_game(self):
        pgn_string = "{ Stockfish 8 64 POPCNT } 1. Nf3 Nf6 2. g3 g6 { A05 King's Indian Attack: Symmetrical Defense } 3. Bg2 Bg7 4. O-O O-O 5. c4 d6 6. b3 e5 7. Bb2 c5 8. e3 Nc6 9. Nc3 Bf5 10. d4 e4 11. Ne1 Re8 12. Nc2 h5 13. Qd2 h4 14. Ba3 $6 { -1.13 } ( 14. h3 g5 15. g4 Bg6 16. Rad1 Qe7 17. Qe2 a6 18. Ba3 a5 { 0.19/25 } ) 14...  b6 $6 { -0.04 } ( 14... Nh7 15. Nd5 Ng5 16. Bb2 Rc8 17. Rac1 Ne7 18. Nf4 h3 19.  Bh1 { -1.11/24 } ) 15. Rfd1 $6 { -1.15 } ( 15. h3 d5 16. g4 Be6 17. cxd5 Nxd5 18. Nxe4 f5 19. gxf5 gxf5 { 0.00/26 } ) 15... Bg4 16. Rdc1 Qd7 17. b4 Qf5 18.  Bb2 Rad8 19. Nb5 Bf3 20. d5 Ne5 $6 { -1.66 } ( 20... Nxb4 21. Ne1 Bxg2 22.  Nxg2 Nd3 23. Nxh4 Qh3 24. Bxf6 Bxf6 25. f4 { -3.14/25 } ) 21. Bxe5 Rxe5 22.  Ne1 hxg3 23. fxg3 Bh6 24. Rab1 Kg7 $6 { -1.08 } ( 24... Qh5 25. Rb3 Rf5 26.  bxc5 dxc5 27. Rc2 Ng4 28. h3 Bxg2 29. Kxg2 { -2.48/24 } ) 25. Rb3 Qh5 26. h3 $6 { -3.08 } ( 26. bxc5 bxc5 27. Nxa7 Rh8 28. h4 Qg4 29. Nc6 Rh5 30. Qf2 Bd1 { -2.00/23 } ) 26... Nh7 $2 { -1.37 } ( 26... Rg5 27. Qf2 { -2.89/24 }) 27. g4 Bxg4 28. hxg4 Qxg4 29. Qd1 $4 { -5.69 } ( 29. Qb2 Ng5 30. Nxd6 Qg3 31. Nf5+ gxf5 32. Kf1 Nf3 33. Qf2 Nh2+ { -2.30/24 } ) 29... Qg3 30. Qe2 Ng5 31. Kh1 Rh8 32. Nxd6 Kg8 33. bxc5 Bf8+ 34. Kg1 Nh3+ 35. Kf1 Bxd6 36. cxd6 Rf5+ 37. Nf3 Rxf3+ 0-1"  # noqa E501
        pgn = StringIO(pgn_string)
        game = shogi.pgn.read_game(pgn)
        result = annotator.game_length(game)
        self.assertEqual(result, 74)


class test_classify_opening(unittest.TestCase):
    pass


class test_add_acpl(unittest.TestCase):
    pass


class test_get_pass1_budget(unittest.TestCase):

    def test_raises_typeerror(self):
        self.assertRaises(TypeError, annotator.get_pass1_budget, 'a')

    def test_math(self):
        seed = random.random()
        result = annotator.get_pass1_budget(seed)
        self.assertEqual(result, seed / 10)


class test_get_pass2_budget(unittest.TestCase):

    def test_raises_typeerror(self):
        self.assertRaises(TypeError, annotator.get_pass2_budget, 1, 'a')

    def test_math(self):
        seed1 = random.random()
        seed2 = random.random()
        result = annotator.get_pass2_budget(seed1, seed2)
        self.assertEqual(result, seed1 - seed2)


class test_get_time_per_move(unittest.TestCase):

    def test_divzero(self):
        pass_budget = "1"
        ply_count = "0"
        self.assertRaises(ZeroDivisionError, annotator.get_time_per_move,
                          pass_budget, ply_count)

    def test_raises_valueerror(self):
        pass_budget = "1"
        ply_count = "a"
        self.assertRaises(ValueError, annotator.get_time_per_move, pass_budget,
                          ply_count)

    def test_returns_float(self):
        pass_budget = "1"
        ply_count = "1"
        result = annotator.get_time_per_move(pass_budget, ply_count)
        assert isinstance(result, float)

    def test_divides_integers(self):
        pass_budget = "12"
        ply_count = "30"
        result = annotator.get_time_per_move(pass_budget, ply_count)
        self.assertEqual(result, 0.4)

    def test_divides_floats(self):
        pass_budget = "15.25"
        ply_count = "20"
        result = annotator.get_time_per_move(pass_budget, ply_count)
        self.assertEqual(result, 0.7625)


class test_analyze_game(unittest.TestCase):
    pass


class test_checkgame(unittest.TestCase):
    pass


class test_eval_human(unittest.TestCase):

    def test_positive_dtm(self):
        score = MagicMock()
        score.mate = 5
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}
        self.assertEqual(annotator.eval_human(True, info_handler), "Mate in 5")
        self.assertEqual(annotator.eval_human(False, info_handler),
                         "Mate in 5")

    def test_negative_dtm(self):
        score = MagicMock()
        score.mate = -5
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}
        self.assertEqual(annotator.eval_human(True, info_handler), "Mate in 5")
        self.assertEqual(annotator.eval_human(False, info_handler),
                         "Mate in 5")

    def test_non_dtm(self):
        score = MagicMock()
        score.mate = None
        score.cp = 100
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}
        self.assertEqual(annotator.eval_human(True, info_handler), "1.00")
        self.assertEqual(annotator.eval_human(False, info_handler), "-1.00")

    def test_raises_runtimeerror(self):
        score = MagicMock()
        score.mate = None
        score.cp = None
        info_handler = MagicMock()
        info_handler.info = {'score': [None, score]}
        self.assertRaises(RuntimeError, annotator.eval_human, True,
                          info_handler)
        self.assertRaises(RuntimeError, annotator.eval_human, False,
                          info_handler)


class test_judge_move(unittest.TestCase):
    pass


# vim: ft=python expandtab smarttab shiftwidth=4 softtabstop=4
