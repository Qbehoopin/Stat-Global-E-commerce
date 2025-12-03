let cart = [];

function addToCart(productName, price) {
  cart.push({ productName, price });
  alert(`${productName} added to cart!`);
  console.log(cart);
}

function submitReview() {
  const name = document.getElementById("reviewerName").value;
  const message = document.getElementById("reviewMessage").value;

  if (name && message) {
    const reviewSection = document.getElementById("dynamicReviews");
    const newReview = document.createElement("div");
    newReview.className = "testimony";
    newReview.innerHTML = `<p>"${message}" – ${name}</p>`;
    reviewSection.appendChild(newReview);

    document.getElementById("reviewerName").value = "";
    document.getElementById("reviewMessage").value = "";
  } else {
    alert("Please fill out both fields.");
  }
}