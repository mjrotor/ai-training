(function(){
  const TOTAL=60,KEY="ai_training_completed";
  function getCompleted(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(e){return[]}}
  function saveCompleted(arr){localStorage.setItem(KEY,JSON.stringify(arr));updateProgress()}
  function updateProgress(){
    const completed=getCompleted();
    const pct=Math.round((completed.length/TOTAL)*100);
    const fill=document.getElementById("progressFill"),text=document.getElementById("progressText");
    if(fill)fill.style.width=pct+"%";if(text)text.textContent=pct+"%";
    for(let i=1;i<=TOTAL;i++){
      const check=document.getElementById("check-"+i),nav=document.querySelector('.nav-item[data-tutorial="'+i+'"]');
      if(!check||!nav)continue;
      if(completed.includes(i)){check.innerHTML="\u2713";nav.classList.add("completed")}
      else{check.innerHTML="";nav.classList.remove("completed")}
    }
    for(let i=1;i<=TOTAL;i++){const s=document.getElementById("status-"+i);if(!s)continue;if(completed.includes(i)){s.innerHTML="<span>\u2705</span> Completed";s.classList.add("done")}}
    document.querySelectorAll(".tutorial-card").forEach(c=>{if(completed.includes(parseInt(c.dataset.tutorial)))c.classList.add("completed")})
  }
  window.goToTutorial=function(n,e){if(e)e.preventDefault();window.location.href="tutorials/"+String(n).padStart(3,"0")+".html"};
  window.markComplete=function(n){const c=getCompleted();if(!completed.includes(n)){c.push(n);saveComplete(c)}if(n<TOTAL)window.location.href="tutorials/"+String(n+1).padStart(3,"0")+".html"};
  window.toggleSidebar=function(){document.getElementById("sidebar").classList.toggle("open");document.getElementById("sidebarOverlay").classList.toggle("show")};
  window.selectQuiz=function(el,qId,isCorrect){
    const parent=el.parentElement;parent.querySelectorAll(".quiz-option").forEach(o=>o.classList.remove("selected","correct","wrong"));
    el.classList.add("selected");const fb=document.getElementById(qId+"-feedback");
    if(isCorrect){el.classList.add("correct");el.classList.remove("wrong");if(fb)fb.innerHTML='<strong style="color:var(--green);">\u2713 Correct!</strong> '+(el.dataset.explain||"")}
    else{el.classList.add("wrong");el.classList.remove("correct");if(fb)fb.innerHTML='<strong style="color:var(--red);">\u2717 Not quite.</strong> Try again.'}
  };
  window.toggleAnswer=function(id){const el=document.getElementById(id);if(el)el.classList.toggle("show")};
  document.addEventListener("DOMContentLoaded",function(){updateProgress()});
})();
