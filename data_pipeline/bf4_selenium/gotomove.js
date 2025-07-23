<script type="text/javascript">

var clickChk = 0;

$(document).ready(function(){  


    
    
        $("#searchKeyword2").hide();
        $("#searchForm #searchWord").show();
    

//자료실
/* 



$("#searchKeyword2").hide();
$("#searchForm #searchWord").show();


 */
    
    var pageReadLen = $("#pageLen").val();
    var bbsEnginePageUnit = "";
    
    if(bbsEnginePageUnit.length>0){
        pageReadLen = bbsEnginePageUnit; 
    }
    
    $("[name='recordCountPerPage']").val(pageReadLen);
    
    $("#reSearch").click(function(){
        var reswTxt = "결과 내 재검색";
        var resw = $(this);
        var reswCtxt = "";
        if(resw.is(":checked")){
            $("#searchForm #searchWord").hide();
            $("#searchKeyword2").show();
            reswCtxt = reswTxt+" (기존 검색어 : "+$("#searchForm #searchWord").val()+")";
        }else{
             $("#searchForm #searchWord").show();
             $("#searchKeyword2").hide();
            reswCtxt = reswTxt;
        }
            resw.next().text(reswCtxt);
    });
});
function goPage(pageNum){   
    if(clickChk == 0){
        clickChk = 2;
    }else if(clickChk == 1){
        alert("검색중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 2){
        alert("페이지 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 3){
        alert("탭 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }
    Header.showLoading();

    var bbsTab = "17";
    
    if(bbsTab==="99"){
        document.listForm.searchKeyword.value = $("#searchForm #searchWord").val();
        document.listForm.searchWord.value = document.listForm.searchKeyword.value;
        document.listForm.searchCondition.value = $("#searchForm #selSearchCondition").val();
        $("[name='listForm'] #pageIndex").val(pageNum);
        $("[name='listForm']").submit();
    }else{
        $("#searchForm #pageIndex").val(pageNum);
        $("#searchForm").attr("action", "InsuAdtCrtrList.do?pgmid=HIRAA030069000400").submit();
    }
}

function doSearch(txt) {    
    if(clickChk == 0){
        clickChk = 1;
    }else if(clickChk == 1){
        alert("검색중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 2){
        alert("페이지 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 3){
        alert("탭 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }
    
    var anum = /^\d+$/;
    
    var pageLen = $("#pageLen").val();
    
    if(txt != "" && txt != null){
        $("#searchWord").val(txt);
    }
    
    
    // 날짜형식 유효성검사
    var datatimeRegexp = /[0-9]{4}-[0-9]{2}-[0-9]{2}/;

    if($("#startDt").val() != ""){
        //if(!anum.test($("#startDt").val())) {
        if(!datatimeRegexp.test($("#startDt").val())) {
            //alert("시행일자는 숫자로만 입력해주세요.");
            alert("날짜는 yyyy-mm-dd 형식으로 입력해주세요.");
            $("#startDt").focus();
            clickChk = 0;
            return;
        }
    }
    if($("#endDt").val() != ""){
        //if(!anum.test($("#endDt").val())) {
        if(!datatimeRegexp.test($("#endDt").val())) {
            //alert("시행일자는 숫자로만 입력해주세요.");
            alert("날짜는 yyyy-mm-dd 형식으로 입력해주세요.");
            $("#endDt").focus();
            clickChk = 0;
            return;
        }
    }
    if($("#startDt").val() > $("#endDt").val()){
        alert("기간 검색 종료일은 시작일 이후로 입력해주시기 바랍니다");
        clickChk = 0;
        return;
    }
    Header.showLoading();
    
    var bbsTab = "17";
    if(bbsTab!=="99"){
        $("[name='recordCountPerPage']").val(pageLen);
        $("#seqListYn").val("N");
        $("#seqList").val("");
        $("#pageIndex").val("1");
        $("#searchYn").val("Y");
        $("#searchForm").attr("action", "InsuAdtCrtrList.do?pgmid=HIRAA030069000400").submit();
    }else{
        document.listForm.startDate.value = $("#startDt").val();
        document.listForm.endDate.value = $("#endDt").val();
        document.listForm.startDt.value = document.listForm.startDate.value;
        document.listForm.endDt.value = document.listForm.endDate.value;
        document.listForm.searchCondition.value = $("#searchForm #selSearchCondition").val();
        document.listForm.searchKeyword.value = $("#searchForm #searchWord").val();
        document.listForm.searchWord.value = document.listForm.searchKeyword.value;
        document.listForm.pageIndex.value ="1";
        document.listForm.action = "";
        document.listForm.submit();
    }
    
}

function viewInsuAdtCrtr(no, mtgHmeDd, sno, mtgMtrRegSno, RN) { 
    var data = "mtgHmeDd="+mtgHmeDd+"&sno="+sno+"&mtgMtrRegSno="+mtgMtrRegSno;
    var option = "width=650,height=706,directories=no,location=no,menubar=no,resizable=no,scrollbars=yes,status=no,titlebar=no,toolbar=no";
    window.open("/rc/insu/insuadtcrtr/InsuAdtCrtrPopup.do?"+data, "insuadtcrtrPopup", option);
}

function goTabMove(tabGbn){ 
    if(clickChk == 0){
        clickChk = 3;
    }else if(clickChk == 1){
        alert("검색중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 2){
        alert("페이지 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }else if(clickChk == 3){
        alert("탭 이동중입니다. 잠시만 기다려주세요.");
        return false;
    }
    Header.showLoading();

    var url = "InsuAdtCrtrList.do?pgmid=HIRAA030069000400";

    if(tabGbn==="99"){
        document.listForm.pageIndex.value ="1";
        document.listForm.tabGbn.value = tabGbn;
        document.listForm.startDate.value = $("#startDt").val();
        document.listForm.endDate.value = $("#endDt").val();
        document.listForm.startDt.value = document.listForm.startDate.value;
        document.listForm.endDt.value = document.listForm.endDate.value;
        document.listForm.searchCondition.value = $("#searchForm #selSearchCondition").val();
        document.listForm.searchKeyword.value = $("#searchForm #searchWord").val();
        document.listForm.searchWord.value = document.listForm.searchKeyword.value;
        document.listForm.pageIndex.value ="1";
        document.listForm.action = "";
        document.listForm.submit();
    }else{
        $("#decIteTpCd").val(tabGbn);
        $("#seqListYn").val("N");
        $("#seqList").val("");
        $("#tabGbn").val(tabGbn);
        $("#pageIndex").val("1");
        $("#searchYn").val("Y");
        $("#searchForm").attr("action", url).submit();
    }
}

function bbsView(pgmid,brdBltNo,pageNo){
    
    var url = "/rc/drug/insuadtcrtr/bbsView.do?pgmid="+pgmid+"&brdScnBltNo=4&brdBltNo="+brdBltNo+"&amp;pageIndex="+pageNo+"&isPopupYn=Y";
    window.open(url,'popup','width=1000,height=700,scrollbars=yes');
}

//반응형 페이징 처리
$(function () {
    window_width = $(window).width();
        if(window_width<800){
            $('#pagingPc').hide();
            $('#pagingM').show();
        }else{
            $('#pagingPc').show();
            $('#pagingM').hide();
        }
    $(window).on('resize', function(){
            window_width = $(window).width();
            if(window_width<800){
                $('#pagingPc').hide();
                $('#pagingM').show();
            }else{
                $('#pagingPc').show();
                $('#pagingM').hide();
            }
    });
});
</script>