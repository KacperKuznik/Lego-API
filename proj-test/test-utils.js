'use strict';

/***
 * Exported functions to be used in the testing scripts.
 */
module.exports = {
  uploadImageBody,
  processUploadReply,
  selectImageToDownload,
  genProductCommentLoop,
  genNewUser,
  genNewUserReply,
  genNewLegoSet,
  genProductComment,
  genNewOldAuction,
  genNewOldBid,
  selectUserMain,
  selectUser,
  selectUserSkewed,
  selectLegoSetFromUserInfo,
  selectLegoSet,
  selectAuction,
  decideNextAction,
  random10,
  random20,
  random50,
  random70,
  random80,
  random90,
  randomLoop20,
  randomLoop50,
  randomLoop70,
  randomLoop80,
  randomLoop90,
  randomLoop95

}


const fs = require('fs')
const { fakerEN, faker, de } = require('@faker-js/faker');

var imagesIds = []
var images = []
var users = []


function genProductCommentText(productName) {
  const template = legoCommentsTemplates.sample();
  return template.replace("{product}", productName);
}

// Auxiliary function to select an element from an array
Array.prototype.sample = function(){
	   return this[Math.floor(Math.random()*this.length)]
}

// Auxiliary function to select an element from an array
Array.prototype.sampleSkewed = function(){
	return this[randomSkewed(this.length)]
}

// Returns a random date
function randomDate() {
	let n = random(13);
	if( n == 0)
		return "12-2023";
	if( n < 10)
		return " " + n.toString()+ "-2024";
	else
		return n.toString()+ "-2024";
}


// Returns a random value, from 0 to val
function random( val){
	return Math.floor(Math.random() * val)
}

// Returns a random value, from 0 to val
function randomSkewed( val){
	let beta = Math.pow(Math.sin(Math.random()*Math.PI/2),2)
	let beta_left = (beta < 0.5) ? 2*beta : 2*(1-beta);
	return Math.floor(beta_left * val)
}

// Loads data about images from disk
function loadData() {
	var i
	var basefile
	if( fs.existsSync( '/images')) 
		basefile = '/images/lego'
	else
		basefile =  'images/lego'	
	for( i = 1; i <= 60 ; i++) {
		var img  = fs.readFileSync(basefile + i + '.jpg')
		images.push( img)
	}
  var str;
  if( fs.existsSync('users.data')) {
    str = fs.readFileSync('users.data','utf8')
    users = JSON.parse(str)
  } 
}

loadData();

/**
 * Sets the body to an image, when using images.
 */
function uploadImageBody(requestParams, context, ee, next) {
	requestParams.body = images.sample()
	return next()
}

/**
 * Process reply of the download of an image. 
 * Update the next image to read.
 */
function processUploadReply(requestParams, response, context, ee, next) {
	if( typeof response.body !== 'undefined' && response.body.length > 0) {
		imagesIds.push(response.body)
	}
    return next()
}

/**
 * Select an image to download.
 */
function selectImageToDownload(context, events, done) {
	if( imagesIds.length > 0) {
		context.vars.imageId = imagesIds.sample()
	} else {
		delete context.vars.imageId
	}
	return done()
}

/**
 * Select an image to download.
 */
function selectUserIds(context, events, done) {
	if( userIds.length > 0) {
		context.vars.userId = userIds.sample()
	} else {
		delete context.vars.userId
	}
	return done()
}

/**
 * Generate data for a new user using Faker
 */
function genNewUser(context, events, done) {
	const first = `${faker.person.firstName()}`
	const last = `${faker.person.lastName()}`
	context.vars.uId = first + "." + last
	context.vars.uName = first + " " + last
	context.vars.uPwd = `${faker.internet.password()}`
	return done()
}


/**
 * Process reply for of new users to store the id on file
 */
function genNewUserReply(requestParams, response, context, ee, next) {
	if( response.statusCode >= 200 && response.statusCode < 300 && response.body.length > 0)  {
		let u = JSON.parse( response.body)
		users.push(u)
		fs.writeFileSync('users.data', JSON.stringify(users));
	}
    return next()
}

/**
 * Generate data for a new legoset using Faker
 */
function genNewLegoSet(context, events, done) {
	context.vars.lsName = `${faker.commerce.productName()}`
	context.vars.lsDescription = `${faker.commerce.productDescription()}`
	return done()
}

/**
 * Generate data for a new legoset comment using Faker
 */
function genProductComment(context, events, done) {
	selectUserRaw(context)
	context.vars.cmtText = genProductCommentText(context.vars.lsName)
	return done()
}

/**
 * Generate data for a new legoset comment when looping
 */
function genProductCommentLoop(context, events, done) {
	context.vars.cmtText = genProductCommentText(context.vars.$loopElement.name)
	return done()
}

/**
 * Generate data for a new auction using Faker
 */
function genNewOldAuction(context, events, done) {
	selectUserRaw(context)
	context.vars.aucStartingPrice = random(50) + 10;
	context.vars.aucLastBid = context.vars.aucStartingPrice - 1;
	var d = new Date();
//	d.setTime(Date.now() - random( 15 * 24 * 60 * 60 * 1000));
	d.setTime(Date.now() + random(5 * 60 * 1000));
	context.vars.aucEndDate = d.toISOString();
	return done()
}


/**
 * Generate data for a new bid using Faker
 */
function genNewOldBid(context, events, done) {
	selectUserRaw(context)
	context.vars.aucLastBid = context.vars.aucLastBid + 1 + random(3);
	return done()
}


/**
 * Select user
 */
function selectUserRaw(context) {
	if( users.length > 0) {
		let user = users.sample()
		context.vars.uId = user.id
		context.vars.uPwd = user.pwd
	} else {
		delete context.vars.uId
		delete context.vars.uPwd
	}
}
function selectUser(context, events, done) {
	selectUserRaw(context)
	return done()
}
function selectUserMain(context, events, done) {
	selectUserRaw(context)
  context.vars.uIdMain = context.vars.uId
  context.vars.uPwdMain = context.vars.uPwd
	return done()
}


/**
 * Select user
 */
function selectUserSkewedRaw(context) {
	if( users.length > 0) {
		let user = users.sampleSkewed()
		context.vars.uId = user.id
		context.vars.uPwd = user.pwd
	} else {
		delete context.vars.uId
		delete context.vars.uPwd
	}
}
function selectUserSkewed(context, events, done) {
	selectUserSkewedRaw(context)
	return done()
}

/**
 * Select legoset from a list of legosets
 * assuming: lego sets context.vars.legoSetLst
 */
function selectLegoSet(context, events, done) {
	if( typeof context.vars.legoSetLst !== 'undefined' && 
			context.vars.legoSetLst.constructor == Array && context.vars.legoSetLst.length > 0) {
		let legoset = context.vars.legoSetLst.sample()
		context.vars.lsId = legoset.id;
		context.vars.lsName = legoset.name;
	} else
		delete context.vars.lsId
	return done()
}

/**
 * Select legoset from userInfo
 */
function selectLegoSetFromUserInfo(context, events, done) {
	if( typeof context.vars.userInfo !== 'undefined' &&
    typeof context.vars.userInfo.legoIds !== 'undefined' && 
			context.vars.userInfo.legoIds.constructor == Array && context.vars.userInfo.legoIds.length > 0) {
		let legosetId = context.vars.userInfo.legoIds.sample()
		context.vars.lsId = legosetId;
	} else
		delete context.vars.lsId
	return done()
}


/**
 * Select auction from a list of auctions
 * assuming: auctions context.vars.auctionLst
 */
function selectAuction(context, events, done) {
	if( typeof context.vars.auctionLst !== 'undefined' && 
			context.vars.auctionLst.constructor == Array && context.vars.auctionLst.length > 0) {
		let auction = context.vars.auctionLst.sample()
		context.vars.auctionId = auction.id;
		context.vars.seller = auction.seller;
    if( typeof auction.highestBid !== 'undefined' && typeof auction.highestBid.amount !== 'undefined')
  	  context.vars.aucLastBid = auction.highestBid.amount + 1 + random(3);
    else
      context.vars.aucLastBid = auction.startingPrice + 1 + random(3);
	} else
		delete context.vars.auctionId
	return done()
}


/**
 * Decide next action: nextAction; afterNextAction
 * 0 -> do nothing  - 40%
 * 1 -> browse next page legoset - 10%
 * 2 -> browse next page auctions - 10%
 * 3 -> check own user - 19%
 * 4 -> check other user - 20%
 * 5 -> create new legoset - 1%
 * 0 or 1,10 -> add comment
 * 0 or 1,14 -> list comments -> 10%
 * 0 or 2,11 -> add bid
 * 0 or 1,12 -> add legoset
 * 3,13 -> create auction - 1% 
 */
function decideNextAction(context, events, done) {
  let rnd = Math.random();
  context.vars.stLegoSets = 0;
  context.vars.stAuctions = 0;
	context.vars.nextAction = 0;
	context.vars.afterNextAction = 0;
	if( rnd < 0.4) {
		context.vars.nextAction = 0;
    if( rnd < 0.04)
      context.vars.afterNextAction = 10;
    else if( rnd < 0.06)
      context.vars.afterNextAction = 11;
    else if( rnd < 0.08)
      context.vars.afterNextAction = 12;
    else if( rnd < 0.18)
      context.vars.afterNextAction = 14;
	} else if( rnd < 0.5) {
		context.vars.nextAction = 1; 
    context.vars.stLegoSets = context.vars.stLegoSets + 20;
    if( rnd < 0.51)
      context.vars.afterNextAction = 10;
    else if( rnd < 0.61)
      context.vars.afterNextAction = 14;
	} else if( rnd < 0.6) {
    context.vars.nextAction = 2;
    context.vars.stAuctions = context.vars.stAuctions + 20;
    if( rnd < 0.61)
      context.vars.afterNextAction = 11;
  } else if( rnd < 0.79) {
    context.vars.nextAction = 3;
    if( rnd < 0.61)
      context.vars.afterNextAction = 13;
    context.vars.uId = context.vars.uIdMain;
  } else if( rnd < 0.99) {
    context.vars.nextAction = 4;
    selectUserRaw(context);
  } else
    context.vars.nextAction = 5;
  return done()
}


/**
 * Set randomValue with probability 10% 
 */
function random10(context, events, done) {
  context.vars.randomValue = Math.random() < 0.1
  return done()
}

/**
 * Set randomValue with probability 20% 
 */
function random20(context, events, done) {
  context.vars.randomValue = Math.random() < 0.2
  return done()
}

/**
 * Set randomValue with probability 50% 
 */
function random50(context, events, done) {
  context.vars.randomValue = Math.random() < 0.5
  return done()
}

/**
 * Set randomValue with probability 70% 
 */
function random70(context, events, done) {
  context.vars.randomValue = Math.random() < 0.7
  return done()
}

/**
 * Set randomValue with probability 80% 
 */
function random80(context, events, done) {
  context.vars.randomValue = Math.random() < 0.8
  return done()
}

/**
 * Set randomValue with probability 90% 
 */
function random90(context, events, done) {
  context.vars.randomValue = Math.random() < 0.9
  return done()
}

/**
 * Return true with probability 20% 
 */
function randomLoop20(context, next) {
  const continueLooping = Math.random() < 0.2
  return next(continueLooping);
}

/**
 * Return true with probability 50% 
 */
function randomLoop50(context, next) {
  const continueLooping = Math.random() < 0.5
  return next(continueLooping);
}

/**
 * Return true with probability 70% 
 */
function randomLoop70(context, next) {
  const continueLooping = Math.random() < 0.7
  return next(continueLooping);
}

/**
 * Return true with probability 70% 
 */
function randomLoop80(context, next) {
  const continueLooping = Math.random() < 0.8
  return next(continueLooping);
}

/**
 * Return true with probability 90% 
 */
function randomLoop90(context, next) {
  const continueLooping = Math.random() < 0.9
  return next(continueLooping);
}

/**
 * Return true with probability 95% 
 */
function randomLoop95(context, next) {
  const continueLooping = Math.random() < 0.95
  return next(continueLooping);
}

const legoCommentsTemplates = [
  // Positive comments
  "I recently purchased the {product} and it was such a fun building experience; the instructions were clear and the pieces fit perfectly.",
  "The {product} is amazing! It took me several hours to assemble, but the end result is absolutely stunning.",
  "I was impressed by the detail and quality of the {product}. It’s both challenging and rewarding to build.",
  "This {product} kept me entertained for hours, and the design is fantastic — I can’t wait to display it on my shelf.",
  "I love the {product}! It’s the perfect mix of creativity and complexity, and every piece feels high-quality.",
  "The {product} is a must-have for LEGO enthusiasts. The building process is smooth and the final model is very impressive.",
  "The {product} offers a great balance of fun and challenge. It’s suitable for both kids and adults who enjoy detailed builds.",
  "Building the {product} was a fantastic experience. The instructions were easy to follow and the pieces are top-quality.",
  "The {product} exceeded my expectations in terms of design, complexity, and overall fun factor.",
  "I bought the {product} as a gift, and it was a huge hit! The recipient couldn’t stop building it.",
  "The {product} is beautiful once completed, and the level of detail is incredible. Definitely worth the price.",
  "I really enjoyed assembling the {product}. It’s challenging enough to be engaging but not frustrating.",
  "The {product} is perfect for LEGO fans of all ages; it’s both fun to build and impressive to display.",
  "I love how the {product} allows for creative additions and modifications after the main build is complete.",
  "I am thrilled with the {product}! It’s an excellent set that combines fun, challenge, and display-worthy results.",
  "The {product} was a joy to build. It kept me engaged for hours, and the final model is very satisfying.",
  "I recommend the {product} to anyone who loves detailed and imaginative LEGO sets.",
  "The {product} has a lot of small details that make it very interesting to assemble and look at afterward.",
  "I love the creativity involved in building the {product}, and it looks amazing on display.",
  "The {product} is quite challenging, but that makes completing it even more rewarding.",
  "The {product} is a great mix of fun and learning; it keeps kids entertained while helping develop problem-solving skills.",
  "The colors and textures of the {product} are very well designed and make the final model look professional.",
  "I’ve built many LEGO sets before, but the {product} stands out for its complexity and visual appeal.",
  "I am amazed at how detailed the {product} is, even in small sections of the build.",
  "The {product} provides hours of entertainment and is a great way to spend time with family or friends.",
  "I love the sense of accomplishment I get after completing the {product}.",
  "The {product} instructions were very thorough, which made the build process enjoyable and stress-free.",
  "The {product} is impressive in every way; the design, challenge, and final display quality are excellent.",
  "I appreciate the level of detail in the {product}, from small decorative elements to larger structural components.",
  "The {product} encourages creativity and allows for some personalization in the build.",
  "I’ve recommended the {product} to all my friends who are LEGO enthusiasts because it’s that good.",
  "I love how the {product} combines mechanical features with aesthetic design elements.",
  "The {product} is very well thought out, with clear instructions and well-fitting pieces.",
  "I enjoyed every moment of building the {product}, and I am proud of the final model.",
  "The {product} is a fantastic gift for LEGO fans, young or old.",
  "Even though the {product} took several hours to complete, it was worth every minute.",
  "I am impressed with how sturdy the {product} is once fully assembled.",
  "The {product} offers a satisfying challenge without being frustrating.",
  "I love displaying the {product} after building it; it’s a real conversation starter.",
  "The {product} provides a fun and engaging experience for LEGO fans of all skill levels.",
  "I highly recommend the {product} to anyone looking for a challenging and enjoyable LEGO set.",
  "The {product} has intricate details that make the build feel more rewarding.",
  "I appreciate the thoughtful design and attention to detail in the {product}.",
  "The {product} is engaging, entertaining, and visually impressive once completed.",
  "The {product} is a great mix of fun, challenge, and aesthetic appeal.",
  "I love the level of creativity that the {product} encourages during the building process.",
  "The {product} is excellent for both individual and group building sessions.",
  "The {product} provides hours of entertainment and a sense of achievement once finished.",
  "The {product} is engaging and well-designed, making it an excellent addition to any LEGO collection.",
  "I am impressed by the complexity and creativity of the {product}.",
  "The {product} is a high-quality set with excellent instructions and well-fitting pieces.",
  "Building the {product} was a joy from start to finish.",
  "The {product} is challenging enough to keep me engaged, but not so hard that it becomes frustrating.",
  "The {product} is suitable for both adults and children who enjoy detailed builds.",
  "I am thrilled with the {product}; it is well-made, fun to build, and looks fantastic when complete.",
  "The {product} is beautifully designed, and the building experience is very enjoyable.",
  "I love how the {product} allows for creative customization after the initial build.",
  "The {product} is impressive in terms of both build quality and final display value.",

  // Neutral comments
  "The {product} is decent; the build was enjoyable, though not as challenging as I expected.",
  "I completed the {product} without any issues, and the final model is satisfactory.",
  "The {product} was fine, but it didn’t stand out compared to other sets I’ve built.",
  "Building the {product} was straightforward, though I wish there were more creative elements.",
  "The {product} is okay; the instructions were clear, and the pieces fit well, but the design is standard.",
  "The {product} provided a moderate challenge, but it was enjoyable overall.",
  "I had an average experience building the {product}; nothing was exceptional, but nothing was bad either.",
  "The {product} looks nice once assembled, but it didn’t impress me greatly.",
  "I am satisfied with the {product}, though it lacks some of the features found in higher-end sets.",
  "The {product} is functional and looks good, but it’s not particularly memorable.",

  // Slightly critical comments
  "The {product} was fun to build, but I found some pieces hard to connect properly.",
  "I expected more from the {product}; while the final model looks okay, the build was somewhat tedious.",
  "The {product} is decent, but I think it is overpriced for what it offers.",
  "Some steps in the {product} instructions were confusing, making the build less smooth than expected.",
  "I enjoyed the {product}, but certain sections felt repetitive and could have been more engaging.",
  "The {product} is okay, but some pieces felt cheap or didn’t fit as well as I would have liked.",
  "I had high expectations for the {product}, but it fell a bit short in terms of design complexity.",
  "The {product} is fun, but I wish there were more interactive elements included.",
  "I completed the {product}, but I think it could have been more challenging to justify the price.",
  "The {product} is enjoyable, yet some small details feel lacking compared to other LEGO sets."
];
