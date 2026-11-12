package eu261_test

import data.eu261

test_late_notice_short_flight_pays_250 if {
	eu261.decision.amount_eur == 250 with input as {
		"departs_eu": true, "disruption": "cancellation", "distance_km": 900,
		"notice_days": 2, "reroute_depart_early_h": 0, "reroute_arrive_late_h": 5,
	}
}

test_two_weeks_notice_pays_nothing if {
	not eu261.eligible with input as {
		"departs_eu": true, "disruption": "cancellation", "distance_km": 900,
		"notice_days": 15,
	}
}

test_close_reroute_long_haul_may_be_halved if {
	d := eu261.decision with input as {
		"departs_eu": true, "disruption": "cancellation", "distance_km": 6000,
		"notice_days": 1, "rerouted": true,
		"reroute_depart_early_h": 3, "reroute_arrive_late_h": 3.5,
	}
	d.amount_eur == 600
	d.carrier_may_halve
}

test_long_haul_delay_under_4h_may_be_halved if {
	d := eu261.decision with input as {
		"departs_eu": true, "disruption": "delay", "distance_km": 6000,
		"arrival_delay_h": 3.5,
	}
	d.amount_eur == 600
	d.carrier_may_halve
}

test_intra_eu_over_3500_km_is_medium if {
	d := eu261.decision with input as {
		"departs_eu": true, "intra_eu": true, "disruption": "delay",
		"distance_km": 4000, "arrival_delay_h": 3,
	}
	d.amount_eur == 400
	not d.carrier_may_halve
}

test_extraordinary_claim_goes_to_a_person if {
	d := eu261.decision with input as {
		"departs_eu": true, "intra_eu": true, "disruption": "delay",
		"distance_km": 2000, "arrival_delay_h": 4, "extraordinary_claimed": true,
	}
	d.needs_human_review
	not d.eligible
}

test_non_eu_carrier_into_eu_is_out_of_scope if {
	not eu261.in_scope with input as {
		"departs_eu": false, "arrives_eu": true, "carrier_is_eu": false,
	}
}