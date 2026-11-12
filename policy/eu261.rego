package eu261

# Facts come from the claim, never from the model's opinion.
# Every rule cites the provision it implements.

default in_scope := false

default eligible := false

default needs_human_review := false

default carrier_may_halve := false

# Art. 3(1)(a): departing from an EU airport
in_scope if input.departs_eu

# Art. 3(1)(b): arriving in the EU on an EU carrier
in_scope if {
	input.arrives_eu
	input.carrier_is_eu
}

# Art. 7(1): distance bands
band := "short" if input.distance_km <= 1500

band := "medium" if {
	input.distance_km > 1500
	input.intra_eu
}

band := "medium" if {
	input.distance_km > 1500
	input.distance_km <= 3500
	not input.intra_eu
}

band := "long" if {
	input.distance_km > 3500
	not input.intra_eu
}

amounts := {"short": 250, "medium": 400, "long": 600}

# Art. 7(2): arrival limits for the carrier's option to halve after re-routing
reduction_limit_h := {"short": 2, "medium": 3, "long": 4}

# Art. 5(1)(c): no compensation if told early enough and re-routed closely enough
cancellation_exempt if input.notice_days >= 14

cancellation_exempt if {
	input.notice_days >= 7
	input.notice_days < 14
	input.reroute_depart_early_h <= 2
	input.reroute_arrive_late_h < 4
}

cancellation_exempt if {
	input.notice_days < 7
	input.reroute_depart_early_h <= 1
	input.reroute_arrive_late_h < 2
}

# Art. 5(1)(c) and 5(3): cancellations
eligible if {
	in_scope
	input.disruption == "cancellation"
	not cancellation_exempt
	not input.extraordinary_claimed
}

# Delays: case law (Sturgeon, C-402/07), not the Regulation's text
eligible if {
	in_scope
	input.disruption == "delay"
	input.arrival_delay_h >= 3
	not input.extraordinary_claimed
}

# Art. 5(3): "extraordinary circumstances" is open-textured, so a person decides
needs_human_review if {
	in_scope
	input.extraordinary_claimed
}

compensation := amounts[band] if eligible

compensation := 0 if not eligible

# Art. 7(2): the carrier MAY halve, so flag the option rather than apply it
carrier_may_halve if {
	eligible
	input.rerouted
	input.reroute_arrive_late_h <= reduction_limit_h[band]
}

# Sturgeon: the same option for long-haul delays of under four hours
carrier_may_halve if {
	eligible
	input.disruption == "delay"
	band == "long"
	input.arrival_delay_h < 4
}

citations contains "Art. 3(1)" if in_scope

citations contains "Art. 5(1)(c)" if cancellation_exempt

citations contains "Art. 5(3)" if input.extraordinary_claimed

citations contains "Art. 7(1)" if eligible

citations contains "Art. 7(2)" if carrier_may_halve

citations contains "Sturgeon, C-402/07" if {
	eligible
	input.disruption == "delay"
}

decision := {
	"eligible": eligible,
	"amount_eur": compensation,
	"carrier_may_halve": carrier_may_halve,
	"needs_human_review": needs_human_review,
	"citations": citations,
}