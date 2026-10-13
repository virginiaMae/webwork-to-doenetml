##DESCRIPTION
##  Precalculus: Domain and range of function
##ENDDESCRIPTION

## KEYWORDS('algebra', 'precalculus', 'function', 'domain', 'range')

## DBsubject('Algebra')
## DBchapter('Functions')
## DBsection('Domain and Range')
## Date('05/18/2010')
## Author('Jonathan Rogness')
## Institution('University of Minnesota')
## TitleText1('Precalculus')
## EditionText1('4')
## AuthorText1('Cohen')
## Section1('3')
## Problem1('')

########################################################################

DOCUMENT();      

loadMacros(
   "PGstandard.pl",     # Standard macros for PG language
   "MathObjects.pl",
   #"source.pl",        # allows code to be displayed on certain sites.
);

########################################################################

TEXT(beginproblem());

$showPartialCorrectAnswers = 1;

##############################################################

Context("Numeric");

$a = random(2,6,1);
$b = random(1,4,1);

$f = Formula("$b*x")->reduce;

$in1 = Interval("(-infinity,5/$b)");
$in2 = Interval("(5/$b, infinity)");

$in3 = Interval("(-infinity,1/$b)");
$in4 = Interval("(1/$b, infinity)");

$ans1 = Union("$in1 U $in2");
$ans2 = Union("$in3 U $in4");

##############################################################

Context()->texStrings;
BEGIN_TEXT
Given \(g(x) = \displaystyle \frac{$a+x}{$f-5}\) answer the following questions.
$HR
$BBOLD 1.$EBOLD What is the domain of \(g(x)\) ? $BR
Answer (in interval notation): \{ans_rule(20)\} $PAR
$BBOLD 2.$EBOLD What is the range of \(g(x)\) ? $BR
Answer (in interval notation): \{ans_rule(20)\}
$HR
END_TEXT
Context()->normalStrings;

##############################################################

Context("Interval");
ANS(($ans1)->cmp(showEndpointHints=>0,showEndTypeHints=>0));
ANS(($ans2)->cmp(showEndpointHints=>0,showEndTypeHints=>0));

ENDDOCUMENT();        