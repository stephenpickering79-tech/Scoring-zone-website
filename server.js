// Simple Express backend for Stripe checkout and webhooks
// Run with: node server.js

const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// create checkout session endpoint
app.post('/create-checkout-session', async (req, res) => {
  try {
    const { priceId, customerEmail } = req.body;

    if (!priceId) {
      return res.status(400).json({ error: 'Price ID is required' });
    }

    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.STRIPE_SUCCESS_URL}?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: process.env.STRIPE_CANCEL_URL,
      customer_email: customerEmail,
      allow_promotion_codes: true,
    });

    res.json({ sessionId: session.id });
  } catch (err) {
    console.error('Error creating checkout session', err);
    res.status(500).json({ error: err.message });
  }
});

// webhook handler
app.post('/webhook', bodyParser.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;

  try {
    event = stripe.webhooks.constructEvent(
      req.body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.log('Webhook signature verification failed.', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  // handle events
  switch (event.type) {
    case 'customer.subscription.created':
      console.log('Subscription created:', event.data.object.id);
      break;
    case 'customer.subscription.updated':
      console.log('Subscription updated:', event.data.object.id);
      break;
    case 'customer.subscription.deleted':
      console.log('Subscription canceled:', event.data.object.id);
      break;
    default:
      console.log(`Unhandled event type ${event.type}`);
  }

  res.json({ received: true });
});

const PORT = process.env.PORT || 4242;
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
