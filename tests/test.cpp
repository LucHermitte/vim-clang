#include <cstddef>
namespace  NS1
{
struct S {
    void f(int i, float);
    void g(double d) const;
    void h(double d) volatile; // cannot detect volatile...
    constexpr auto i(double d = 12.5) { return 42 * d;}

    virtual int pure() = 0;
    virtual int v();

    template <typename T, std::size_t N> void t(T element, unsigned u, double const& d);

    S() noexcept = default;
    void wi() noexcept(true);
    void wi2() noexcept(false);

    explicit S(double);
};

constexpr bool Toto = false;
struct S0 {
    S0() = delete;
    virtual int v(double d);
    virtual int v_pub_pri();
    virtual int pure() = 0;
private:
    virtual int constone(S const& s) const noexcept(Toto) = 0;
};

struct S2 : S0 {
    int v(double d) override;
private:
    int v_pub_pri() override;
    int pure() final;
public:
    class C {
        C() = default;
        static void f();
    };
};

struct S3 : S2, private S2::C
{
};

template <typename T, int N> struct array {
    void f() {
        int i;
    }
    T tab[N];
};
}

