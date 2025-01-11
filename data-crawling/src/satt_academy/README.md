#### Need to process
1. replace 1+ spaces with 1 space
2. remove leading and trailing spaces
3. for each word detect lang, if 20% > !bengali, then remove
4. remove qna which are english
5. "\"টিওয়াইসি স্পোর্টস' কোন দেশভিত্তিক সংবাদমাধ্যম?" -> "টিওয়াইসি স্পোর্টস কোন দেশভিত্তিক সংবাদমাধ্যম?"
6. "সম্প্রতি গুগল কতজন কর্মীকে ছাটাই করেছে?" --> need to remove these "current" type questions
7 "জাতিসংঘের উন্নয়ন কর্মসূচি (UNDP)- এর বর্তমান মহাস- চিব কে?" --> "জাতিসংঘের উন্নয়ন কর্মসূচি (UNDP)- এর বর্তমান মহাসচিব কে?"
8. if categories has "English" then remove