// helper fetch
async function postAnalyze(payload) {
  const res = await fetch("/analyze", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  return await res.json();
}

// *** NEW HELPER FUNCTION TO CALL /chat ***
async function postChat(payload) {
  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  return await res.json();
}

function formatRupee(x) {
  return "₹" + Number(x).toLocaleString();
}

function speakText(text) {
  // Choose a female voice if available
  const synth = window.speechSynthesis;
  let voices = synth.getVoices();
  if (!voices.length) {
    // some browsers require onvoiceschanged
    synth.onvoiceschanged = () => { voices = synth.getVoices(); speakText(text); };
    return;
  }
  // prefer known female voice names or ones with 'female' keyword
  let voice = voices.find(v => /female|zira|samantha|google uk english female|australia/i.test(v.name.toLowerCase()));
  if (!voice) {
    // fallback to the first voice that contains 'English' (more natural)
    voice = voices.find(v => /english/i.test(v.lang)) || voices[0];
  }
  const utter = new SpeechSynthesisUtterance(text);
  utter.voice = voice;
  utter.lang = voice.lang || 'en-IN';
  utter.rate = 1.0;
  utter.pitch = 1.05;
  synth.speak(utter);
}

// Build friendly HTML for plan objects (no brackets)
function renderKeyValueBlock(containerId, obj, titleMap = {}) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  Object.keys(obj).forEach(k => {
    const label = titleMap[k] || k.replace(/_/g," ").replace(/\b\w/g, c => c.toUpperCase());
    const val = typeof obj[k] === "number" ? formatRupee(obj[k]) : obj[k];
    const row = document.createElement("div");
    row.className = "flex justify-between py-1";
    row.innerHTML = `<span class="text-sm text-gray-600">${label}</span><span class="font-medium">${val}</span>`;
    container.appendChild(row);
  });
}

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const payload = {
    user_id: document.getElementById("user_id").value || "demo_user",
    age: Number(document.getElementById("age").value || 25),
    income: Number(document.getElementById("income").value || 0),
    fixed_expenses: Number(document.getElementById("fixed_expenses").value || 0),
    variable_expenses: Number(document.getElementById("variable_expenses").value || 0),
    debt: Number(document.getElementById("debt").value || 0),
    credit_score: Number(document.getElementById("credit_score").value || 650),
    dependents: Number(document.getElementById("dependents").value || 0),
    risk_tolerance: document.getElementById("risk_tolerance").value,
    investment_experience: document.getElementById("investment_experience").value,
    savings_goal: Number(document.getElementById("savings_goal").value || 0),
    savings_target_months: Number(document.getElementById("savings_target_months").value || 12)
  };

  if (payload.income <= 0) { alert("Please enter a positive monthly income."); return; }

  const data = await postAnalyze(payload);

  document.getElementById("report").classList.remove("hidden");
  document.getElementById("risk_label").textContent = data.risk.label;
  document.getElementById("risk_score").textContent = data.risk.score + " / 100";
  document.getElementById("predicted_expense").textContent = formatRupee(data.predicted_expense);
  document.getElementById("ef_target").textContent = formatRupee(data.emergency_fund.target) + ` (${data.emergency_fund.months} months)`;
  document.getElementById("disposable").textContent = formatRupee(data.disposable_income);

  // render budget plans cleanly (no brackets)
  renderKeyValueBlock("budget50", data.budget_50_30_20, {"needs":"Needs","wants":"Wants","savings":"Savings (50/30/20)"});
  renderKeyValueBlock("customBudget", data.custom_budget, {"essentials":"Essentials","variable":"Variable","disposable":"Disposable","suggest_savings":"Suggested savings"});

  // debt and savings
  document.getElementById("debt_plan").textContent = data.debt_plan.note;
  document.getElementById("invest_alloc").innerHTML = "";
  Object.entries(data.investment_allocation).forEach(([k,v])=>{
    const div = document.createElement("div");
    div.className = "flex justify-between py-1";
    div.innerHTML = `<span class="text-sm text-gray-600">${k.replace(/_/g,' ')}</span><span class="font-medium">${v}%</span>`;
    document.getElementById("invest_alloc").appendChild(div);
  });
  document.getElementById("savings_plan").textContent = data.savings_plan.message ? data.savings_plan.message : `Save ₹${data.savings_plan.suggested_monthly} / month to reach goal in ${data.savings_plan.months_target} months (needs ₹${data.savings_plan.monthly_needed}/mo).`;

  // advice
  const advList = document.getElementById("advice_list");
  advList.innerHTML = "";
  data.advice.forEach(a => {
    const li = document.createElement("li"); li.textContent = a; advList.appendChild(li);
  });

  // extras: practical ways to earn + links + books
  const extras = document.getElementById("extras");
  extras.innerHTML = "";
  // simple ideas
  const ideas = [
    {title:"Start a skill-based freelance gig (e.g., coding, design, tutoring)", notes:"Platforms: Upwork, Fiverr, Freelancer"},
    {title:"Teach what you know (tutoring or mini-courses)", notes:"Use YouTube / Udemy / local coaching"},
    {title:"Part-time content creation (YouTube/Shorts) on a niche you enjoy", notes:"Monetize via ads/affiliate income"},
    {title:"Micro-investing / dividend investing", notes:"Start with low-cost index ETFs; avoid high-risk day trading"},
    {title:"Sell digital goods (templates, presets, guides)", notes:"Use Gumroad / Etsy / Shopify"}
  ];
  ideas.forEach(it => {
    const el = document.createElement("div");
    el.className = "py-1";
    el.innerHTML = `<div class="font-medium">${it.title}</div><div class="text-sm text-gray-600">${it.notes}</div>`;
    extras.appendChild(el);
  });

  // resources (links & books)
  const resDiv = document.createElement("div");
  resDiv.className = "mt-3";
  resDiv.innerHTML = `<h4 class="font-semibold">Learning Links & Books</h4>`;
  const ul = document.createElement("ul");
  ul.className = "list-disc pl-5";
  (data.resources || []).forEach(r => {
    const li = document.createElement("li");
    li.innerHTML = `<a href="${r.url}" target="_blank" class="text-blue-600 underline">${r.title}</a>`;
    ul.appendChild(li);
  });
  resDiv.appendChild(ul);
  extras.appendChild(resDiv);

  // allocation chart
  const alloc = data.investment_allocation;
  const allocLabels = Object.keys(alloc);
  const allocValues = allocLabels.map(k => alloc[k]);
  const ctx = document.getElementById("allocationChart").getContext("2d");
  if (window.allocChart) window.allocChart.destroy();
  window.allocChart = new Chart(ctx, {type:'doughnut', data:{labels:allocLabels, datasets:[{data:allocValues}]}, options:{responsive:true, plugins:{legend:{position:'bottom'}}}});

  // history chart (line)
  const history = data.history || [];
  const labels = history.map(h => new Date(h.t).toLocaleString());
  const incomes = history.map(h => h.income);
  const expenses = history.map(h => h.expenses);
  const debts = history.map(h => h.debt);
  const ctx2 = document.getElementById("historyChart").getContext("2d");
  if (window.histChart) window.histChart.destroy();
  window.histChart = new Chart(ctx2, {
    type: 'line',
    data: { labels: labels, datasets: [
      { label: 'Income', data: incomes, borderColor: 'green', fill:false },
      { label: 'Expenses', data: expenses, borderColor: 'red', fill:false },
      { label: 'Debt', data: debts, borderColor: 'orange', fill:false }
    ]},
    options: { responsive:true, plugins:{legend:{position:'bottom'}}}
  });

  // prepare friendly assistant summary
  const summary = `Hi — I checked your finances. Your risk level is ${data.risk.label} (${data.risk.score} percent). Next month's predicted expense is ${formatRupee(data.predicted_expense)}. ${data.advice.slice(0,2).join(' ')} I also added practical earning ideas and learning links below. Would you like me to explain any part in detail?`;
  window.latestAssistantSummary = summary;
  // auto-speak short friendly summary
  speakText(summary);
});

// *** UPDATED ASSISTANT BUTTON LOGIC ***
document.getElementById("speakBtn").addEventListener("click", async () => {
  // if we have a latest summary, speak it, else prompt analyze first
  if (window.latestAssistantSummary) {
    speakText(window.latestAssistantSummary + " You can ask me questions about your report — just type them now.");
    
    // open a prompt for user question
    const q = prompt("Ask FINESIGHT a question about your finances (e.g., 'how to reduce expenses by 20%'):");
    if (!q) return; // User cancelled prompt

    // NEW: Call the backend /chat endpoint
    const chatPayload = {
      user_id: document.getElementById("user_id").value || "demo_user",
      question: q
    };
    
    // Show loading state (optional, but good)
    const originalAlert = "FINESIGHT — Assistant reply:\n\n";
    alert(originalAlert + "Thinking...");
    
    const data = await postChat(chatPayload);
    const reply = data.response; // Get smart reply from backend

    // speak and show the smart alert
    speakText(reply);
    alert(originalAlert + reply);
    
  } else {
    alert("Run analysis first so I have context about your finances.");
  }
});