module register8 (
    input  logic       clk,
    input  logic       rst,
    input  logic [7:0]  d,
    output logic [7:0]  q
);
  always_ff @(posedge clk) begin
    if (rst) q <= '0;
    else     q <= d;
  end
endmodule
