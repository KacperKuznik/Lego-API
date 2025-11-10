'use strict';

const { faker } = require('@faker-js/faker');
const path = require('path');
const fs = require('fs');
const FormData = require('form-data');
const axios = require("axios");

module.exports = {
	generateUserData,
	fetchAllUsers,
	getUserId,
	generateLegoSetData,
	fetchAllLegoSetIds,
	selectLegoSetId,
	createLegoSet,
	generateListingData
};


function generateUserData(context, events, done) {
  context.vars.nickname = faker.internet.username();
  context.vars.name = faker.person.fullName();
	context.vars.password = faker.internet.password(12);
	return done()
}

async function fetchAllUsers(context, events, done) {
	const baseUrl = process.env.TARGET_URL;
	try {
    const res = await fetch(`${baseUrl}/user`);
    const users = await res.json();
    context.vars.userIds = users.map(u => u.id);
  } catch (err) {
    context.vars.userIds = [];
  }
  context.vars.userCount = context.vars.userIds.length;
}

 function getUserId(context, events, done) {
  if (context.vars.userIds && context.vars.userIds.length > 0) {
    context.vars.userId = context.vars.userIds.pop();
  } else {
    context.vars.userId = null;
  }
  return done()
}

function generateLegoSetData(context, events, done) {
  context.vars.legoSetName = "legoset";
  context.vars.legoSetCode = faker.number.int({ min: 1, max: 10000 }).toString();
  context.vars.legoSetDescription = faker.commerce.productDescription();
  context.vars.ownerId = context.vars.userId || null;
  return done();
}



const folderPath = path.join(__dirname, "images");
const files = fs.readdirSync(folderPath).map(file => path.join(folderPath, file));

async function createLegoSet(context, events, done) {
  const baseUrl = process.env.TARGET_URL;
  const formData = new FormData();
  formData.append("name", context.vars.legoSetName);
  formData.append("code_number", context.vars.legoSetCode);
  formData.append("description", context.vars.legoSetDescription);
  formData.append("owner_id", context.vars.ownerId);

	files.slice(0, 3).forEach(filePath => {
	formData.append("files", fs.createReadStream(filePath));
	});
	

  try {
    const response = await axios.post(`${baseUrl}/legoset/`, formData, {
      headers: formData.getHeaders(),
	});
	  legoId = response.data.id
  } catch (err) {
  }
};

async function fetchAllLegoSetIds(context, events, done) {
  const baseUrl = process.env.TARGET_URL;

  try {
    const res = await fetch(`${baseUrl}/legoset`);
    const legosets = await res.json();
    context.vars.legoSetIds = legosets.map(l => l.id);
  } catch (err) {
    context.vars.legoSetIds = [];
  }
}

function selectLegoSetId(context, events) {
  if (context.vars.legoSetIds && context.vars.legoSetIds.length > 0) {
    context.vars.legoSetId = context.vars.legoSetIds[0];
  } else {
    context.vars.legoSetId = null;
  }
	  return done()
}

function generateListingData(context, events, done) {
  context.vars.legoset_id = faker.datatype.number({ min: 1, max: 100 }).toString();
  context.vars.seller_id = faker.datatype.number({ min: 1, max: 50 }).toString();
  context.vars.base_price = faker.finance.amount(10, 500, 2);
  context.vars.close_date = faker.date.soon(30).toISOString();
  context.vars.status = faker.helpers.arrayElement(["open", "closed", "pending"]);
  
  return done();
}