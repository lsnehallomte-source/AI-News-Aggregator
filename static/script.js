let news = [];
let sentimentChart = null;

fetch("/api/news")
  .then(response => response.json())
  .then(data => {
    news = data;
    showNews(news);
  })
  .catch(error => console.error("Error loading news:", error));

const container = document.getElementById("newsContainer");

function showNews(data){

container.innerHTML="";

let positive=0;
let neutral=0;
let negative=0;

data.forEach(item=>{

if(item.sentiment==="Positive") positive++;
else if(item.sentiment==="Neutral") neutral++;
else negative++;

let categoryClass= "tech";

if(item.category==="Finance")
categoryClass="finance";

if(item.category==="Sports")
categoryClass="sports";

let sentimentClass=item.sentiment.toLowerCase();

container.innerHTML+=`

<div class="card">

<img src="${item.image || 'https://placehold.co/300x180?text=No+Image'}" alt="News Image">

<h2>${item.title}</h2>

<span class="badge ${categoryClass}">
${item.category}
</span>

<span class="badge ${sentimentClass}">
${item.sentiment}
</span>

<p><strong>Source:</strong> ${item.source}</p>

<p><strong>Published:</strong> ${new Date(item.publishedAt).toLocaleString()}</p>

<p>${item.description}</p>

<a href="${item.url}" target="_blank">
    <button>Read More</button>
</a>

<button onclick='bookmarkNews(${JSON.stringify(item)})'>
    ⭐ Bookmark
</button>

</div>

`;

});

document.getElementById("totalNews").textContent=data.length;
document.getElementById("positiveCount").textContent=positive;
document.getElementById("neutralCount").textContent=neutral;
document.getElementById("negativeCount").textContent=negative;

if (sentimentChart) {
    sentimentChart.destroy();
}

const ctx = document.getElementById("sentimentChart");

sentimentChart = new Chart(ctx, {
    type: "pie",
    data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{
            data: [positive, neutral, negative]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

}

showNews(news);

document.getElementById("searchInput").addEventListener("keyup",function(){

const value=this.value.toLowerCase();

const filtered=news.filter(item=>

item.title.toLowerCase().includes(value) ||

item.category.toLowerCase().includes(value)

);

showNews(filtered);

})
function filterCategory(category) {

    if (category === "All") {
        showNews(news);
        return;
    }

    const filtered = news.filter(item =>
        item.category === category
    );

    showNews(filtered);
}
function bookmarkNews(item) {

    fetch("/bookmark", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: item.title,
            image: item.image,
            url: item.url,
            source: item.source,
            category: item.category,
            sentiment: item.sentiment
        })
    })

    .then(response => response.json())
    .then(data => {
        alert(data.message);
    });

}