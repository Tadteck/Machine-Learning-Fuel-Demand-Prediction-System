from marshmallow import Schema, fields, ValidationError

class PredictionInputSchema(Schema):
    temperature = fields.Float(required=True)
    holiday = fields.Integer(required=True)
    fuel_price = fields.Float(required=True)

class UpdateDataSchema(Schema):
    temperature = fields.Float(required=True)
    holiday = fields.Integer(required=True)
    fuel_price = fields.Float(required=True)
    demand = fields.Float(required=True)