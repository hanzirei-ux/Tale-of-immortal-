#include "catalog_utils.hpp"
#include <cassert>
#include <iostream>
int main(){
    toi::CatalogQuery q;
    assert(toi::parseCatalogQuery("@-1||0",q));assert(q.type==-1&&q.term.empty()&&q.offset==0);
    assert(toi::parseCatalogQuery("@2|Blade|40",q));assert(q.type==2&&q.term=="Blade"&&q.offset==40);
    for(auto bad:{"","2|test|0","@x|a|0","@-2||0","@2|a|xyz","@2|a|-1","@2|a|40x","@2|a|40|2","@2|a|100001"})assert(!toi::parseCatalogQuery(bad,q));
    assert(toi::matchRank("Crescent Blade","101","cres")==0);
    assert(toi::matchRank("Crescent Blade","101","blade")==1);
    assert(toi::matchRank("Crescent Blade","101","102")==-1);
    assert(toi::matchRank("Crescent Blade","101","10")==0);
    assert(toi::safeCatalogName("A\\tB\\nC")=="A\\tB\\nC");
    assert(toi::safeCatalogName("A\tB\nC") == "A B C");
    std::cout<<"catalog parsing, autocomplete ordering, sanitation: PASS\n";
}
