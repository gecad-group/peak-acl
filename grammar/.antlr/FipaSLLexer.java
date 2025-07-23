// Generated from c:/Users/santi/Desktop/peak-acl/grammar/FipaSL.g4 by ANTLR 4.13.1
import org.antlr.v4.runtime.Lexer;
import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.Token;
import org.antlr.v4.runtime.TokenStream;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.misc.*;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast", "CheckReturnValue", "this-escape"})
public class FipaSLLexer extends Lexer {
	static { RuntimeMetaData.checkVersion("4.13.1", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		LPAREN=1, RPAREN=2, QUOTE=3, NUMBER=4, SYMBOL=5, WS=6, COMMENT=7;
	public static String[] channelNames = {
		"DEFAULT_TOKEN_CHANNEL", "HIDDEN"
	};

	public static String[] modeNames = {
		"DEFAULT_MODE"
	};

	private static String[] makeRuleNames() {
		return new String[] {
			"LPAREN", "RPAREN", "QUOTE", "NUMBER", "SYMBOL", "WS", "COMMENT"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
			null, "'('", "')'"
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, "LPAREN", "RPAREN", "QUOTE", "NUMBER", "SYMBOL", "WS", "COMMENT"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}


	public FipaSLLexer(CharStream input) {
		super(input);
		_interp = new LexerATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@Override
	public String getGrammarFileName() { return "FipaSL.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public String[] getChannelNames() { return channelNames; }

	@Override
	public String[] getModeNames() { return modeNames; }

	@Override
	public ATN getATN() { return _ATN; }

	public static final String _serializedATN =
		"\u0004\u0000\u0007E\u0006\uffff\uffff\u0002\u0000\u0007\u0000\u0002\u0001"+
		"\u0007\u0001\u0002\u0002\u0007\u0002\u0002\u0003\u0007\u0003\u0002\u0004"+
		"\u0007\u0004\u0002\u0005\u0007\u0005\u0002\u0006\u0007\u0006\u0001\u0000"+
		"\u0001\u0000\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0002\u0001\u0002"+
		"\u0001\u0002\u0005\u0002\u0018\b\u0002\n\u0002\f\u0002\u001b\t\u0002\u0001"+
		"\u0002\u0001\u0002\u0001\u0003\u0003\u0003 \b\u0003\u0001\u0003\u0004"+
		"\u0003#\b\u0003\u000b\u0003\f\u0003$\u0001\u0003\u0001\u0003\u0004\u0003"+
		")\b\u0003\u000b\u0003\f\u0003*\u0003\u0003-\b\u0003\u0001\u0004\u0001"+
		"\u0004\u0005\u00041\b\u0004\n\u0004\f\u00044\t\u0004\u0001\u0005\u0004"+
		"\u00057\b\u0005\u000b\u0005\f\u00058\u0001\u0005\u0001\u0005\u0001\u0006"+
		"\u0001\u0006\u0005\u0006?\b\u0006\n\u0006\f\u0006B\t\u0006\u0001\u0006"+
		"\u0001\u0006\u0000\u0000\u0007\u0001\u0001\u0003\u0002\u0005\u0003\u0007"+
		"\u0004\t\u0005\u000b\u0006\r\u0007\u0001\u0000\u0006\u0002\u0000\"\"\\"+
		"\\\u0001\u000009\u0003\u0000AZ__az\u0005\u0000--09AZ__az\u0003\u0000\t"+
		"\n\r\r  \u0002\u0000\n\n\r\rM\u0000\u0001\u0001\u0000\u0000\u0000\u0000"+
		"\u0003\u0001\u0000\u0000\u0000\u0000\u0005\u0001\u0000\u0000\u0000\u0000"+
		"\u0007\u0001\u0000\u0000\u0000\u0000\t\u0001\u0000\u0000\u0000\u0000\u000b"+
		"\u0001\u0000\u0000\u0000\u0000\r\u0001\u0000\u0000\u0000\u0001\u000f\u0001"+
		"\u0000\u0000\u0000\u0003\u0011\u0001\u0000\u0000\u0000\u0005\u0013\u0001"+
		"\u0000\u0000\u0000\u0007\u001f\u0001\u0000\u0000\u0000\t.\u0001\u0000"+
		"\u0000\u0000\u000b6\u0001\u0000\u0000\u0000\r<\u0001\u0000\u0000\u0000"+
		"\u000f\u0010\u0005(\u0000\u0000\u0010\u0002\u0001\u0000\u0000\u0000\u0011"+
		"\u0012\u0005)\u0000\u0000\u0012\u0004\u0001\u0000\u0000\u0000\u0013\u0019"+
		"\u0005\"\u0000\u0000\u0014\u0015\u0005\\\u0000\u0000\u0015\u0018\t\u0000"+
		"\u0000\u0000\u0016\u0018\b\u0000\u0000\u0000\u0017\u0014\u0001\u0000\u0000"+
		"\u0000\u0017\u0016\u0001\u0000\u0000\u0000\u0018\u001b\u0001\u0000\u0000"+
		"\u0000\u0019\u0017\u0001\u0000\u0000\u0000\u0019\u001a\u0001\u0000\u0000"+
		"\u0000\u001a\u001c\u0001\u0000\u0000\u0000\u001b\u0019\u0001\u0000\u0000"+
		"\u0000\u001c\u001d\u0005\"\u0000\u0000\u001d\u0006\u0001\u0000\u0000\u0000"+
		"\u001e \u0005-\u0000\u0000\u001f\u001e\u0001\u0000\u0000\u0000\u001f "+
		"\u0001\u0000\u0000\u0000 \"\u0001\u0000\u0000\u0000!#\u0007\u0001\u0000"+
		"\u0000\"!\u0001\u0000\u0000\u0000#$\u0001\u0000\u0000\u0000$\"\u0001\u0000"+
		"\u0000\u0000$%\u0001\u0000\u0000\u0000%,\u0001\u0000\u0000\u0000&(\u0005"+
		".\u0000\u0000\')\u0007\u0001\u0000\u0000(\'\u0001\u0000\u0000\u0000)*"+
		"\u0001\u0000\u0000\u0000*(\u0001\u0000\u0000\u0000*+\u0001\u0000\u0000"+
		"\u0000+-\u0001\u0000\u0000\u0000,&\u0001\u0000\u0000\u0000,-\u0001\u0000"+
		"\u0000\u0000-\b\u0001\u0000\u0000\u0000.2\u0007\u0002\u0000\u0000/1\u0007"+
		"\u0003\u0000\u00000/\u0001\u0000\u0000\u000014\u0001\u0000\u0000\u0000"+
		"20\u0001\u0000\u0000\u000023\u0001\u0000\u0000\u00003\n\u0001\u0000\u0000"+
		"\u000042\u0001\u0000\u0000\u000057\u0007\u0004\u0000\u000065\u0001\u0000"+
		"\u0000\u000078\u0001\u0000\u0000\u000086\u0001\u0000\u0000\u000089\u0001"+
		"\u0000\u0000\u00009:\u0001\u0000\u0000\u0000:;\u0006\u0005\u0000\u0000"+
		";\f\u0001\u0000\u0000\u0000<@\u0005;\u0000\u0000=?\b\u0005\u0000\u0000"+
		">=\u0001\u0000\u0000\u0000?B\u0001\u0000\u0000\u0000@>\u0001\u0000\u0000"+
		"\u0000@A\u0001\u0000\u0000\u0000AC\u0001\u0000\u0000\u0000B@\u0001\u0000"+
		"\u0000\u0000CD\u0006\u0006\u0000\u0000D\u000e\u0001\u0000\u0000\u0000"+
		"\n\u0000\u0017\u0019\u001f$*,28@\u0001\u0006\u0000\u0000";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}